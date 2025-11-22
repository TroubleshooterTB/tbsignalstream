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

# It's good practice to import any necessary external modules, like an ATR calculator
# from technical_indicators import calculate_atr # Assuming a helper library

class PositionManager:
    """
    Manages the state and lifecycle of all open and closed trades.
    """

    def __init__(self):
        """Initializes the PositionManager."""
        self.open_positions: List[Dict[str, Any]] = []
        self.closed_positions: List[Dict[str, Any]] = []
        self.trade_id_counter: int = 0

    def is_position_open(self, symbol: str) -> bool:
        """Checks if there is an active position for a given symbol."""
        return any(p['symbol'] == symbol and p['status'] == 'open' for p in self.open_positions)

    def get_all_positions_as_dataframe(self) -> pd.DataFrame:
        """Returns a DataFrame of all open and closed positions for logging."""
        if not self.open_positions and not self.closed_positions:
            return pd.DataFrame()
        return pd.DataFrame(self.open_positions + self.closed_positions)

    def open_position(self, symbol: str, pattern_details: Dict[str, Any], entry_bar_index: int):
        """
        Opens a new trade and adds it to the list of open positions.
        This is called by the main bot logic after a trade is validated.
        """
        self.trade_id_counter += 1
        position = {
            "trade_id": self.trade_id_counter,
            "symbol": symbol,
            "status": "open",
            "direction": pattern_details.get('breakout_direction', 'up'),
            "entry_price": pattern_details.get('breakout_price'),
            "entry_bar_index": entry_bar_index,
            "initial_stop_loss": pattern_details.get('initial_stop_loss'),
            "current_stop_loss": pattern_details.get('initial_stop_loss'), # Initially the same
            "profit_target": pattern_details.get('calculated_price_target'), # Primary target for scaling out
            "pattern_details": pattern_details,
            "size_percentage": 1.0, # Starts with 100% of the position
            "entry_timestamp": pd.Timestamp.now(),
            "pnl_percentage": 0.0
        }
        self.open_positions.append(position)
        print(f"POSITION_MANAGER: Opened new {position['direction'].upper()} position for {symbol} (Trade ID: {self.trade_id_counter}) at {position['entry_price']:.2f}.")

    def manage_open_positions(self, market_data: pd.DataFrame, execution_manager, active_persona) -> Optional[float]:
        """
        The core loop for managing all active trades.
        This method is called on every new bar of market data.
        """
        if not self.open_positions:
            return None

        latest_bar = market_data.iloc[-1]
        closed_trade_pnl = None

        for position in self.open_positions[:]: # Iterate over a copy
            if position['status'] != 'open':
                continue

            # --- Check 1: False Breakout on the very next bar ---
            if market_data.index[-1] == position['entry_bar_index'] + 1:
                if execution_manager.check_for_false_breakout(market_data, position['pattern_details']):
                    print(f"POSITION_MANAGER: Closing position {position['trade_id']} due to False Breakout.")
                    closed_trade_pnl = self._close_position(position, latest_bar['Close'], "closed_false_breakout")
                    continue

            # --- Check 2: Stop-Loss Hit ---
            if (position['direction'] == 'up' and latest_bar['Low'] <= position['current_stop_loss']) or \
               (position['direction'] == 'down' and latest_bar['High'] >= position['current_stop_loss']):
                print(f"POSITION_MANAGER: Closing position {position['trade_id']} due to Stop-Loss hit at {position['current_stop_loss']:.2f}.")
                closed_trade_pnl = self._close_position(position, position['current_stop_loss'], "closed_stop_loss")
                continue
            
            # --- Check 3: Profit Target & Scaling Out ---
            # As per the "Day Trading Strategies" PDF, we scale out to lock in profits.
            if position['size_percentage'] == 1.0: # Only scale out once
                if (position['direction'] == 'up' and latest_bar['High'] >= position['profit_target']) or \
                   (position['direction'] == 'down' and latest_bar['Low'] <= position['profit_target']):
                    print(f"POSITION_MANAGER: Profit Target {position['profit_target']:.2f} hit for trade {position['trade_id']}. Scaling out 50%.")
                    # In a real system, this would log a partial profit.
                    position['size_percentage'] = 0.5 
                    # After scaling out, we move the stop to breakeven to make the rest of the trade risk-free.
                    position['current_stop_loss'] = position['entry_price']
                    print(f"POSITION_MANAGER: Stop-Loss for trade {position['trade_id']} moved to breakeven at {position['entry_price']:.2f}.")

            # --- Check 4: Trailing Stop-Loss Management for the remainder of the position ---
            if position['size_percentage'] < 1.0:
                self._update_trailing_stop(position, market_data, active_persona)
        
        return closed_trade_pnl


    def _close_position(self, position: Dict[str, Any], exit_price: float, reason: str) -> float:
        """
        Internal helper to close a position and move it to the closed list.
        """
        position['status'] = reason
        position['exit_price'] = exit_price
        position['exit_timestamp'] = pd.Timestamp.now()
        
        pnl_percentage = (exit_price - position['entry_price']) / position['entry_price']
        if position['direction'] == 'down':
            pnl_percentage = -pnl_percentage

        position['pnl_percentage'] = pnl_percentage
        
        self.closed_positions.append(position)
        self.open_positions.remove(position)
        
        return pnl_percentage

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculates the Average True Range (ATR) for the given data."""
        if len(data) < period:
            return None
        high_low = data['High'] - data['Low']
        high_close = (data['High'] - data['Close'].shift()).abs()
        low_close = (data['Low'] - data['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        # Use simple moving average for ATR calculation as it's common
        atr = true_range.rolling(window=period).mean()
        return atr.iloc[-1]

    def _update_trailing_stop(self, position: Dict[str, Any], market_data: pd.DataFrame, active_persona):
        """
        Updates the trailing stop-loss based on volatility (ATR).
        This logic is derived from professional trading principles.
        """
        # A real implementation would get the ATR multiple from the active_persona
        atr_multiple = 2.0 # Example: 2x ATR trailing stop

        # Calculate ATR on recent data. In a real system, this would be pre-calculated.
        atr = self._calculate_atr(market_data.iloc[-15:])
        if atr is None or atr == 0:
            return

        trailing_distance = atr * atr_multiple
        latest_close = market_data['Close'].iloc[-1]

        if position['direction'] == 'up':
            new_trailing_stop = latest_close - trailing_distance
            # The stop can only move up, never down.
            if new_trailing_stop > position['current_stop_loss']:
                position['current_stop_loss'] = new_trailing_stop
                print(f"POSITION_MANAGER: Trailing Stop for trade {position['trade_id']} updated to {new_trailing_stop:.2f}.")
        elif position['direction'] == 'down':
            new_trailing_stop = latest_close + trailing_distance
            # The stop can only move down, never up.
            if new_trailing_stop < position['current_stop_loss']:
                position['current_stop_loss'] = new_trailing_stop
                print(f"POSITION_MANAGER: Trailing Stop for trade {position['trade_id']} updated to {new_trailing_stop:.2f}.")


# Example Usage
if __name__ == '__main__':
    # This block is for testing this module in isolation.
    # It demonstrates the lifecycle of a trade from open to close.
    
    # Mock dependencies
    class MockExecutionManager:
        def check_for_false_breakout(self, data, details): return False
    
    class MockPersona:
        pass

    pm = PositionManager()
    exec_mgr = MockExecutionManager()
    persona = MockPersona()

    mock_pattern = {
        'pattern_name': 'Test Pattern', 'breakout_direction': 'up',
        'breakout_price': 100.0, 'initial_stop_loss': 98.0,
        'calculated_price_target': 105.0,
        'pattern_top_boundary': 100.0, 'pattern_bottom_boundary': 95.0
    }

    # 1. Open a position
    pm.open_position("TEST.NS", mock_pattern, entry_bar_index=0)
    print(f"Open positions: {len(pm.open_positions)}")

    # 2. Simulate a few bars of price moving in our favor
    market_data_1 = pd.DataFrame({'High': [102.0], 'Low': [99.0], 'Close': [101.5]}, index=[1])
    pm.manage_open_positions(market_data_1, exec_mgr, persona)

    # 3. Simulate hitting the profit target
    print("\n--- Simulating Profit Target Hit ---")
    market_data_2 = pd.DataFrame({'High': [105.5], 'Low': [101.0], 'Close': [105.2]}, index=[2])
    pm.manage_open_positions(market_data_2, exec_mgr, persona)
    print(f"Position size after scaling out: {pm.open_positions[0]['size_percentage']}")
    print(f"New Stop-Loss: {pm.open_positions[0]['current_stop_loss']}")

    # 4. Simulate hitting the new trailing stop-loss
    print("\n--- Simulating Trailing Stop-Loss Hit ---")
    market_data_3 = pd.DataFrame({'High': [106.0], 'Low': [99.5], 'Close': [100.0]}, index=[3]) # Low hits the breakeven stop
    pm.manage_open_positions(market_data_3, exec_mgr, persona)

    print(f"\nOpen positions: {len(pm.open_positions)}")
    print("Final Positions State:")
    print(pm.get_all_positions_as_dataframe())
