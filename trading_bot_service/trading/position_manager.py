# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Expert Module: Position Manager (position_manager.py)
#
# This module is the bot's risk and trade management brain. It embodies the
# discipline from the trading guides, managing every trade's lifecycle from
# the moment it's opened until it's closed. It handles stop-losses, profit-
# taking, scaling out, and trailing stops with precision.
# ==============================================================================

import pandas as pd
from typing import Dict, Any, List, Optional
import numpy as np
import logging

# Configuration values (inline to avoid cross-module dependencies)
POSITION_MANAGEMENT = {
    'ATR_PERIOD': 14,
    'TRAILING_STOP_ATR_FACTOR': 2.0,
    'SCALE_OUT_PERCENTAGE': 0.5,
}

RISK_SETTINGS = {
    'RISK_PER_TRADE_PERCENT': 1.0,
    'ACCOUNT_EQUITY': 100000.0,
}

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PositionManager:
    """
    Manages the state and lifecycle of all open and closed trades.
    """

    def __init__(self):
        """Initializes the PositionManager with configurable parameters."""
        self.open_positions: List[Dict[str, Any]] = []
        self.closed_positions: List[Dict[str, Any]] = []
        self.trade_id_counter: int = 0
        
        # Load parameters from inline config
        self.atr_period = POSITION_MANAGEMENT['ATR_PERIOD']
        self.trailing_stop_atr_factor = POSITION_MANAGEMENT['TRAILING_STOP_ATR_FACTOR']
        self.scale_out_percentage = POSITION_MANAGEMENT['SCALE_OUT_PERCENTAGE']
        
        logging.info("PositionManager initialized with configurations.")

    def is_position_open(self, symbol: str) -> bool:
        """Checks if there is an active position for a given symbol."""
        return any(p['symbol'] == symbol and p['status'] == 'open' for p in self.open_positions)

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Returns a list of all open positions."""
        return self.open_positions.copy()

    def get_all_positions_as_dataframe(self) -> pd.DataFrame:
        """Returns a DataFrame of all open and closed positions for logging."""
        if not self.open_positions and not self.closed_positions:
            return pd.DataFrame() # Return empty DataFrame if no positions
        return pd.DataFrame(self.open_positions + self.closed_positions)

    def open_position(self, symbol: str, pattern_details: Dict[str, Any], entry_bar_index: int, entry_price: float, position_size: int):
        """
        Opens a new trade and adds it to the list of open positions.
        This is called by the main bot logic after a trade is validated.

        Args:
            symbol: The trading symbol.
            pattern_details: Dictionary from PatternDetector with pattern information.
            entry_bar_index: The index of the bar on which the entry occurred.
            entry_price: The actual price at which the position was opened.
            position_size: The number of shares/units to trade (calculated based on risk).
        """
        self.trade_id_counter += 1
        position = {
            "trade_id": self.trade_id_counter,
            "symbol": symbol,
            "status": "open",
            "direction": pattern_details.get('breakout_direction', 'up'),
            "entry_price": entry_price,
            "entry_bar_index": entry_bar_index,
            "initial_stop_loss": pattern_details.get('initial_stop_loss'),
            "current_stop_loss": pattern_details.get('initial_stop_loss'), # Initialize current stop
            "fibonacci_targets": pattern_details.get('fibonacci_targets', []), # Get targets
            "pattern_details": pattern_details,
            "size": position_size, # Actual number of shares/units
            "remaining_size": position_size, # Tracks remaining size after scaling out
            "entry_timestamp": pd.Timestamp.now(),
            "scaled_out_at_target_index": -1,
            "pnl_at_scale_out": 0.0 # To track P&L on scaled out portion
        }

        # Sort Fibonacci targets: ascending for 'up' direction, descending for 'down'
        if position['direction'] == 'up':
            position['fibonacci_targets'] = sorted(position['fibonacci_targets'], key=lambda x: x['price'])
        else:
            position['fibonacci_targets'] = sorted(position['fibonacci_targets'], key=lambda x: x['price'], reverse=True)

        self.open_positions.append(position)
        logging.info(f"POSITION_MANAGER: Opened new position {position['trade_id']} ({position['direction']}) of {position['size']} units at {position['entry_price']:.2f} for {position['symbol']}. Initial Stop: {position['initial_stop_loss']:.2f}")


    def manage_open_positions(self, market_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        The core loop for managing all active trades on each new bar.
        Checks for stop loss, false breakout, and profit targets/trailing stops.

        Args:
            market_data: The latest DataFrame of price history (OHLCV), including the current bar.

        Returns:
            A list of dictionaries for any closed trades in this cycle, with their P&L.
        """
        closed_trades_info = []
        if not self.open_positions or market_data.empty:
            return closed_trades_info

        latest_bar = market_data.iloc[-1]

        # Need enough data to calculate ATR for trailing stops and false breakouts
        current_atr = self._calculate_atr(market_data, period=self.atr_period)
        if current_atr is None:
             logging.warning("POSITION_MANAGER: Insufficient data for full position management (need more bars for ATR). Proceeding with basic stop checks.")


        for position in self.open_positions[:]: # Iterate over a copy to allow removal
            if position['status'] != 'open':
                continue

            # --- Phase 1: Immediate False Breakout Check (only on the very next bar after entry) ---
            # This check is crucial and typically occurs on the bar immediately following entry.
            # The `entry_bar_index` and `current_bar_index` are used to determine if it's the 'next' bar.
            current_bar_index = market_data.index[-1] # Assuming market_data index is comparable or sequential bar numbers
            
            # Convert DataFrame index to a comparable number if it's a DatetimeIndex for direct comparison
            if isinstance(current_bar_index, pd.Timestamp):
                # If the index is datetime, we need to compare its position in the series
                # This is a robust way to check if current bar is the one directly after entry
                try:
                    current_bar_idx_in_series = data.index.get_loc(current_bar_index)
                    if current_bar_idx_in_series == position['entry_bar_index'] + 1:
                         # This means current bar is the first bar AFTER entry bar
                         # Perform false breakout check
                         if self._check_false_breakout(position, latest_bar):
                             logging.info(f"POSITION_MANAGER: Closing position {position['trade_id']} due to False Breakout.")
                             closed_trades_info.append(self._close_position(position, latest_bar['Close'], "closed_false_breakout"))
                             continue # Move to the next position if closed
                except KeyError: # current_bar_index might not be directly found in series if it's a new bar outside the original data range
                    pass # Skip check if index handling is complex, rely on other stops
            else: # Assuming integer/sequential index comparison
                if current_bar_index == position['entry_bar_index'] + 1:
                    if self._check_false_breakout(position, latest_bar):
                        logging.info(f"POSITION_MANAGER: Closing position {position['trade_id']} due to False Breakout.")
                        closed_trades_info.append(self._close_position(position, latest_bar['Close'], "closed_false_breakout"))
                        continue

            # --- Phase 2: Profit Target & Scaling Out ---
            # Iterate through Fibonacci targets.
            for i, target in enumerate(position.get('fibonacci_targets', [])): 
                if i <= position['scaled_out_at_target_index']: 
                    continue # Skip targets already scaled out at

                target_price = target['price']

                target_hit = False
                if position['direction'] == 'up' and latest_bar['High'] >= target_price:
                    target_hit = True
                elif position['direction'] == 'down' and latest_bar['Low'] <= target_price:
                    target_hit = True

                if target_hit:
                    logging.info(f"POSITION_MANAGER: Fibonacci Target {target['level']} ({target_price:.2f}) hit for trade {position['trade_id']}.")
                    
                    if position['remaining_size'] > 0 and position['scaled_out_at_target_index'] == -1: # Only scale out at first target if not already
                        scaled_out_size = int(position['size'] * self.scale_out_percentage)
                        if scaled_out_size == 0 and position['size'] > 0: scaled_out_size = 1 # Ensure at least 1 unit if position exists
                        
                        # Update remaining size
                        position['remaining_size'] -= scaled_out_size
                        if position['remaining_size'] < 0: position['remaining_size'] = 0 # Prevent negative size

                        position['scaled_out_at_target_index'] = i # Mark this target as scaled out
                        
                        # Calculate P&L for the scaled out portion
                        pnl_scaled_out_percent = ((target_price - position['entry_price']) / position['entry_price']) * 100.0
                        if position['direction'] == 'down': pnl_scaled_out_percent = -pnl_scaled_out_percent
                        position['pnl_at_scale_out'] = pnl_scaled_out_percent

                        logging.info(f"POSITION_MANAGER: Scaling out {scaled_out_size} units ({self.scale_out_percentage*100:.0f}%) at {target_price:.2f} for trade {position['trade_id']}. Remaining: {position['remaining_size']} units.")
                        
                        # Move the stop to breakeven for the remaining position
                        position['current_stop_loss'] = position['entry_price']
                        logging.info(f"POSITION_MANAGER: Stop-Loss for trade {position['trade_id']} moved to breakeven at {position['entry_price']:.2f}.")
                        
                        # After scaling out, the remaining position is managed by the trailing stop.
                        break # Exit target loop after scaling out at the first hit target
                    else:
                         logging.info(f"POSITION_MANAGER: Subsequent target {target['level']} hit, trailing stop is managing the rest or already scaled out.")

            # --- Phase 3: Trailing Stop-Loss Management (for remaining size) ---
            if position['remaining_size'] > 0 and current_atr is not None and current_atr > 0:
                self._update_trailing_stop(position, latest_bar, current_atr)
            elif position['remaining_size'] == 0: # If full position scaled out, close it from open list
                if position['status'] == 'open': # Only close if still marked open
                    logging.info(f"POSITION_MANAGER: All units scaled out for trade {position['trade_id']}. Moving to closed positions.")
                    closed_trades_info.append(self._close_position(position, latest_bar['Close'], "closed_all_scaled_out")) # Close with latest price as exit
                    continue # Skip final stop check as it's closed

            # --- Phase 4: Final Stop-Loss Check (Initial, Breakeven, or Trailing) ---
            if position['status'] == 'open' and position['remaining_size'] > 0: 
                stop_loss_hit = False
                if position['direction'] == 'up' and latest_bar['Low'] <= position['current_stop_loss']:
                    stop_loss_hit = True
                elif position['direction'] == 'down' and latest_bar['High'] >= position['current_stop_loss']:
                    stop_loss_hit = True

                if stop_loss_hit:
                    logging.info(f"POSITION_MANAGER: Closing position {position['trade_id']} due to Stop-Loss hit at {position['current_stop_loss']:.2f}.")
                    # Use the stop loss price as the exit price when stopped out
                    closed_trades_info.append(self._close_position(position, position['current_stop_loss'], "closed_stop_loss"))
                    continue # Move to the next position if closed
        
        return closed_trades_info


    def _close_position(self, position: Dict[str, Any], exit_price: float, reason: str) -> Dict[str, Any]:
        """
        Internal helper to close a position and move it to the closed list.

        Args:
            position: The position dictionary to close.
            exit_price: The price at which the position was closed.
            reason: The reason for closing (e.g., 'closed_stop_loss', 'closed_target', 'closed_false_breakout').

        Returns:
            The updated position dictionary that was closed.
        """
        position['status'] = reason
        position['exit_price'] = exit_price
        position['exit_timestamp'] = pd.Timestamp.now()

        # Calculate P&L for the remaining portion or full initial size if no scale out
        # This P&L is for the portion being closed now.
        pnl_actual_percent = ((exit_price - position['entry_price']) / position['entry_price']) * 100.0
        if position['direction'] == 'down':
            pnl_actual_percent = -pnl_actual_percent # Reverse P&L for short positions

        position['pnl_percentage'] = pnl_actual_percent # P&L for the part being closed
        
        # If this is the final closure (remaining_size > 0 before this call implies not all scaled out)
        if position['remaining_size'] > 0 and reason != "closed_all_scaled_out":
             # Adjust P&L for the *remaining* portion if it's explicitly stopped out
             # For simplicity, we'll assign the P&L of the stop-out to the whole original trade for logging purposes
             # More granular tracking would be needed for complex P&L reporting of partial exits.
             position['final_pnl_percent'] = pnl_actual_percent # This is the final P&L for the entire trade for reporting
        elif reason == "closed_all_scaled_out":
             # If it's a full scale out, the P&L is the average P&L of scaled out portions (simplified to first target P&L for now)
             position['final_pnl_percent'] = position['pnl_at_scale_out']
        else:
             position['final_pnl_percent'] = pnl_actual_percent # Should be for initial stop out or final exit

        self.closed_positions.append(position)
        if position in self.open_positions:
            self.open_positions.remove(position)

        logging.info(f"POSITION_MANAGER: Trade {position['trade_id']} closed at {exit_price:.2f} for reason: {reason}. P&L: {position['final_pnl_percent']:.2f}%. Remaining size: {position['remaining_size']}")

        return position # Return the full closed position info


    def _calculate_atr(self, data: pd.DataFrame, period: int) -> Optional[float]:
        """Calculates the Average True Range (ATR) for the given data."""
        if len(data) < period + 1: 
            return None

        for col in ['High', 'Low', 'Close']:
             if col not in data.columns: return None
             data[col] = pd.to_numeric(data[col], errors='coerce')
        data.dropna(subset=['High', 'Low', 'Close'], inplace=True)

        if len(data) < period + 1:
             return None

        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift(1)).abs().fillna(0)
        low_close = (data['Low'] - data['Close'].shift(1)).abs().fillna(0)
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr.iloc[-1]


    def _update_trailing_stop(self, position: Dict[str, Any], latest_bar: pd.Series, current_atr: float):
        """
        Updates the trailing stop-loss for a position using ATR.

        Args:
            position: The position dictionary.
            latest_bar: The pandas Series for the latest bar.
            current_atr: The calculated ATR for the current bar.
        """
        if current_atr <= 0: return

        if position['direction'] == 'up':
            new_trailing_stop = latest_bar['Close'] - (current_atr * self.trailing_stop_atr_factor)
            # Ensure stop only moves up and respects previous stop levels (initial or breakeven)
            min_stop_level = max(position['initial_stop_loss'], position['entry_price'] if position['scaled_out_at_target_index'] != -1 else -np.inf)
            position['current_stop_loss'] = max(position['current_stop_loss'], new_trailing_stop, min_stop_level)

        elif position['direction'] == 'down':
            new_trailing_stop = latest_bar['Close'] + (current_atr * self.trailing_stop_atr_factor)
            # Ensure stop only moves down and respects previous stop levels (initial or breakeven)
            max_stop_level = min(position['initial_stop_loss'], position['entry_price'] if position['scaled_out_at_target_index'] != -1 else np.inf)
            position['current_stop_loss'] = min(position['current_stop_loss'], new_trailing_stop, max_stop_level)

        # logging.debug(f"POSITION_MANAGER: Trade {position['trade_id']}: Trailing stop updated to {position['current_stop_loss']:.2f}")

    def _check_false_breakout(self, position: Dict[str, Any], latest_bar: pd.Series) -> bool:
        """
        Checks for a false breakout on the bar immediately following the entry.
        This is a crucial and often immediate exit condition.

        Args:
            position: The position dictionary.
            latest_bar: The pandas Series for the bar immediately after entry.

        Returns:
            True if a false breakout is detected, False otherwise.
        """
        pattern_details = position.get('pattern_details', {})
        breakout_direction = position['direction']
        entry_price = position['entry_price']
        latest_close = latest_bar['Close']
        
        # A false breakout occurs if the price immediately reverses and closes significantly
        # back inside the pattern or beyond the entry point in the wrong direction.
        # This requires the pattern's original boundaries.
        top_boundary = pattern_details.get('pattern_top_boundary')
        bottom_boundary = pattern_details.get('pattern_bottom_boundary')

        if top_boundary is None or bottom_boundary is None: 
            logging.warning("POSITION_MANAGER: False breakout check skipped, pattern boundaries not defined.")
            return False

        # For an upward breakout, if price closes back below the top boundary or significantly below entry
        if breakout_direction == 'up':
            if latest_close < top_boundary or latest_close < entry_price * 0.995: # Close back below boundary or significant reversal below entry
                return True
        # For a downward breakout, if price closes back above the bottom boundary or significantly above entry
        elif breakout_direction == 'down':
            if latest_close > bottom_boundary or latest_close > entry_price * 1.005: # Close back above boundary or significant reversal above entry
                return True
        return False


# Example Usage
if __name__ == '__main__':
    # This block is for testing this module in isolation.
    # It demonstrates the lifecycle of a trade from open to close.

    # Mock data stream and setup
    mock_data_stream_prices = [
        100.0, 101.5, 102.0, 105.0, 104.0, 103.0, 100.0, 99.0, 98.0, 97.0, 95.0, 93.0, 90.0, 88.0, 85.0
    ]
    mock_data_stream_volume = [
        1000, 1200, 1100, 2000, 1300, 1100, 1500, 1400, 1300, 1200, 1800, 1700, 2500, 2200, 3000
    ]
    mock_data_ohlcv = []
    for i, price in enumerate(mock_data_stream_prices):
        mock_data_ohlcv.append({
            'Open': price - np.random.rand() * 2,
            'High': price + np.random.rand() * 2,
            'Low': price - np.random.rand() * 2 - 1,
            'Close': price,
            'Volume': mock_data_stream_volume[i] 
        })
    full_mock_data = pd.DataFrame(mock_data_ohlcv)
    # Ensure data has enough history for ATR period
    if len(full_mock_data) < POSITION_MANAGEMENT['ATR_PERIOD'] + 5: # Add some buffer
        extra_bars = POSITION_MANAGEMENT['ATR_PERIOD'] + 5 - len(full_mock_data)
        extra_data = pd.DataFrame({
            'Open': np.random.rand(extra_bars) * 5 + 90,
            'High': np.random.rand(extra_bars) * 5 + 95,
            'Low': np.random.rand(extra_bars) * 5 + 85,
            'Close': np.random.rand(extra_bars) * 5 + 90,
            'Volume': np.random.randint(500, 1000, extra_bars)
        })
        full_mock_data = pd.concat([extra_data, full_mock_data], ignore_index=True)
    
    # Set a sequential integer index for easy testing in this block
    full_mock_data.index = range(len(full_mock_data))

    pm = PositionManager()

    # Mock pattern details including Fibonacci targets
    mock_pattern = {
        'pattern_name': 'Test Bull Flag', 
        'breakout_direction': 'up',
        'breakout_price': 100.0, 
        'initial_stop_loss': 98.0,
        'fibonacci_targets': [{'level': '0.618', 'price': 104.0}, {'level': '1.0', 'price': 108.0}],
        'pattern_top_boundary': 100.5, 
        'pattern_bottom_boundary': 99.5 # Needed for false breakout check
    }

    # 1. Open a position
    entry_bar_idx = full_mock_data.index[POSITION_MANAGEMENT['ATR_PERIOD'] + 2] # Some bar after ATR period
    entry_price = full_mock_data['Close'].iloc[entry_bar_idx]
    position_size = 100 # Example size
    pm.open_position("TEST.NS", mock_pattern, entry_bar_index=entry_bar_idx, entry_price=entry_price, position_size=position_size)

    logging.info(f"\nOpen positions after opening: {len(pm.open_positions)}")
    if pm.open_positions:
        logging.info(f"Initial Stop Loss: {pm.open_positions[0]['current_stop_loss']:.2f}")


    # 2. Simulate bar-by-bar management
    logging.info("\n--- Simulating Bar-by-Bar Management ---")
    closed_positions_history = []

    for i in range(entry_bar_idx + 1, len(full_mock_data)):
        current_data_subset = full_mock_data.iloc[:i+1]
        latest_bar_close = current_data_subset['Close'].iloc[-1]
        logging.info(f"\nProcessing bar index: {i}. Latest Close: {latest_bar_close:.2f}")

        newly_closed_trades = pm.manage_open_positions(current_data_subset)
        if newly_closed_trades:
            closed_positions_history.extend(newly_closed_trades)

        if pm.open_positions:
             logging.info(f"Current Stop Loss: {pm.open_positions[0]['current_stop_loss']:.2f}. Current Remaining Size: {pm.open_positions[0]['remaining_size']}")
        else:
             logging.info("No open positions.")
             # If all positions are closed, we can stop the simulation early
             if not closed_positions_history and i < len(full_mock_data) -1: # if nothing closed yet, but sim is running out, keep going
                 pass
             else:
                break

    logging.info(f"\nOpen positions at the end: {len(pm.open_positions)}")
    logging.info("\nFinal All Positions State (DataFrame):")
    print(pm.get_all_positions_as_dataframe())
