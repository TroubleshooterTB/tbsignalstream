# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Expert Module: Execution Manager (execution_manager.py)
#
# This module is the bot's "judgment." It acts as the final gatekeeper,
# applying extra layers of confirmation to ensure every trade signal is of
# the highest possible quality. It embodies the principles of confluence and
# trading with the dominant trend from the expert trading guides.
# ==============================================================================

import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, Tuple

class ExecutionManager:
    """
    Handles the final entry and risk validation logic for trade execution.
    Implements advanced confirmation checks like Indicator Confluence and MTFA.
    """

    def __init__(self):
        """Initializes the ExecutionManager with standard, proven parameters."""
        self.mtfa_period = 50
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

    def validate_trade_entry(self, data_5min: pd.DataFrame, data_60min: pd.DataFrame, pattern_details: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Applies final validation checks to confirm a trade entry signal.

        Args:
            data_5min: The 5-minute price/volume data for the trading chart.
            data_60min: The 60-minute price/volume data for higher time frame analysis.
            pattern_details: Dictionary from patterns.py.

        Returns:
            A tuple containing:
            - bool: True if the trade entry is valid, False otherwise.
            - str: A reason for the validation decision.
        """
        if not pattern_details:
            return False, "No pattern details provided."

        direction = pattern_details.get('breakout_direction')
        if not direction:
            return False, "Pattern details missing 'breakout_direction'."

        # --- Check 1: Multiple Time Frame Analysis (MTFA) ---
        # A core principle: The bot must trade in the direction of the dominant, higher time frame trend.
        mtfa_check, mtfa_reason = self._confirm_mtfa_alignment(data_60min, direction)
        if not mtfa_check:
            return False, f"MTFA FAILED: {mtfa_reason}"
        print(f"EXECUTION_MANAGER: MTFA PASSED - {mtfa_reason}")

        # --- Check 2: Indicator Confluence ---
        # The breakout pattern must be confirmed by underlying market momentum.
        indicator_check, indicator_reason = self._confirm_indicator_confluence(data_5min, direction)
        if not indicator_check:
            return False, f"INDICATOR CONFLUENCE FAILED: {indicator_reason}"
        print(f"EXECUTION_MANAGER: INDICATOR CONFLUENCE PASSED - {indicator_reason}")
        
        return True, "All validation checks passed. Trade is confirmed."

    def _confirm_mtfa_alignment(self, data_60min: pd.DataFrame, direction: str) -> Tuple[bool, str]:
        """Checks if the trade direction aligns with the 60-minute trend."""
        if len(data_60min) < self.mtfa_period:
            return False, "Not enough 60-min data for MTFA."

        # Calculate the 50-period EMA on the 60-minute chart
        # The 'ta' library automatically handles column names.
        data_60min.ta.ema(length=self.mtfa_period, append=True)
        ema_col_name = f"EMA_{self.mtfa_period}"
        
        latest_close_60min = data_60min['Close'].iloc[-1]
        latest_ema_60min = data_60min[ema_col_name].iloc[-1]

        if direction == 'up':
            if latest_close_60min > latest_ema_60min:
                return True, "Price is above 60-min EMA."
            else:
                return False, "Price is below 60-min EMA; long trade contradicts dominant trend."
        elif direction == 'down':
            if latest_close_60min < latest_ema_60min:
                return True, "Price is below 60-min EMA."
            else:
                return False, "Price is above 60-min EMA; short trade contradicts dominant trend."
        return False, "Invalid direction for MTFA."

    def _confirm_indicator_confluence(self, data_5min: pd.DataFrame, direction: str) -> Tuple[bool, str]:
        """Checks if momentum indicators (MACD, RSI) support the trade direction."""
        if len(data_5min) < self.macd_slow:
            return False, "Not enough 5-min data for indicators."

        # Calculate MACD using pandas_ta
        data_5min.ta.macd(fast=self.macd_fast, slow=self.macd_slow, signal=self.macd_signal, append=True)
        macd_line_col = f'MACD_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        signal_line_col = f'MACDs_{self.macd_fast}_{self.macd_slow}_{self.macd_signal}'
        
        macd_line = data_5min[macd_line_col].iloc[-1]
        signal_line = data_5min[signal_line_col].iloc[-1]
        
        # Calculate RSI using pandas_ta
        data_5min.ta.rsi(length=self.rsi_period, append=True)
        rsi_col = f'RSI_{self.rsi_period}'
        rsi = data_5min[rsi_col].iloc[-1]

        if direction == 'up':
            if macd_line <= signal_line:
                return False, "MACD is not in a bullish state (MACD line is not above signal line)."
            if rsi >= self.rsi_overbought:
                return False, f"RSI is overbought ({rsi:.2f}), indicating upward exhaustion and high risk."
            return True, "MACD is bullish and RSI is not overbought."
            
        elif direction == 'down':
            if macd_line >= signal_line:
                return False, "MACD is not in a bearish state (MACD line is not below signal line)."
            if rsi <= self.rsi_oversold:
                return False, f"RSI is oversold ({rsi:.2f}), indicating downward exhaustion and high risk."
            return True, "MACD is bearish and RSI is not oversold."
            
        return False, "Invalid direction for indicator confluence."

    def check_for_false_breakout(self, data_after_entry: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """Checks for a false breakout on the bar immediately following trade entry."""
        latest_close = data_after_entry['Close'].iloc[-1]
        breakout_direction = pattern_details.get('breakout_direction')
        top_boundary = pattern_details.get('pattern_top_boundary')
        bottom_boundary = pattern_details.get('pattern_bottom_boundary')

        if breakout_direction == 'up' and latest_close < top_boundary:
            return True
        elif breakout_direction == 'down' and latest_close > bottom_boundary:
            return True
        return False

# Example Usage
if __name__ == '__main__':
    # This block is for testing this module in isolation.
    
    # Create sample data
    # 60-min data shows a clear uptrend (price above EMA)
    data_60m = pd.DataFrame({'Close': pd.Series(range(100, 160))})
    
    # 5-min data for a bullish setup
    close_prices_bull = pd.Series([150, 151, 150.5, 152, 151.5, 153, 152.5, 154, 153.5, 155] * 3)
    data_5m_bull = pd.DataFrame({'Close': close_prices_bull})
    
    mock_pattern_bullish = {'pattern_name': 'Bull Flag', 'breakout_direction': 'up'}
    mock_pattern_bearish = {'pattern_name': 'Head/Shoulders', 'breakout_direction': 'down'}

    exec_mgr = ExecutionManager()

    print("--- Testing Valid Bullish Trade ---")
    is_valid, reason = exec_mgr.validate_trade_entry(data_5m_bull, data_60m, mock_pattern_bullish)
    print(f"Validation Result: {is_valid}, Reason: {reason}")

    print("\n--- Testing Invalid Bearish Trade (contradicts 60-min trend) ---")
    is_valid, reason = exec_mgr.validate_trade_entry(data_5m_bull, data_60m, mock_pattern_bearish)
    print(f"Validation Result: {is_valid}, Reason: {reason}")
