# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Expert Module: Pattern Detector (patterns.py) - vX Grandmaster Edition
#
# This module contains the deep knowledge for identifying classic and advanced
# technical analysis chart patterns based on the provided PDF guides. It is the
# primary "eyes" of the trading bot.
# ==============================================================================

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.signal import find_peaks

class PatternDetector:
    """
    Scans market data to identify high-probability chart patterns with precision.
    Each detection function is a specialist for a specific pattern.
    """

    def __init__(self):
        """Initializes the master pattern detector."""
        # A list of all specialist detection methods to run.
        self.pattern_scanners = [
            self.detect_head_and_shoulders,
            self.detect_ascending_triangle,
            # Add other implemented pattern functions here as they are built
        ]

    def scan(self, market_data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """
        Runs all available pattern scanners on the latest market data.

        Args:
            market_data: The DataFrame of price history (OHLCV).
            symbol: The symbol of the stock being analyzed.

        Returns:
            A dictionary containing the details of the first confirmed pattern found,
            or an empty dictionary if no patterns are confirmed.
        """
        for scanner in self.pattern_scanners:
            pattern_details = scanner(market_data)
            if pattern_details:
                # A pattern has been detected and confirmed by a breakout.
                return pattern_details
        return {}

    # --- Specialist Pattern Detection Functions ---

    def detect_head_and_shoulders(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects a Head and Shoulders Top pattern with precision.
        This is a highly reliable bearish reversal pattern.
        """
        if len(data) < 60: return None # Need sufficient data for multiple pivots

        # Use scipy to find peaks (shoulders and head)
        # The prominence parameter is crucial for filtering out minor wiggles
        peaks, _ = find_peaks(data['High'], prominence=data['High'].std() * 0.75, width=5)
        troughs, _ = find_peaks(-data['Low'], prominence=data['Low'].std() * 0.75, width=5)

        if len(peaks) < 3 or len(troughs) < 2: return None

        # Identify the last three significant peaks as potential H&S
        last_three_peaks_indices = peaks[-3:]
        left_shoulder_idx, head_idx, right_shoulder_idx = last_three_peaks_indices
        
        left_shoulder_price = data['High'].iloc[left_shoulder_idx]
        head_price = data['High'].iloc[head_idx]
        right_shoulder_price = data['High'].iloc[right_shoulder_idx]

        # Core H&S Geometry Rules from guides:
        # 1. Head must be the highest peak.
        if not (head_price > left_shoulder_price and head_price > right_shoulder_price):
            return None
            
        # 2. Shoulders should be roughly symmetrical in price.
        if not (abs(left_shoulder_price - right_shoulder_price) / head_price < 0.15): # Allow 15% variance
            return None

        # 3. Find the troughs between the peaks to define the neckline.
        troughs_between = troughs[(troughs > left_shoulder_idx) & (troughs < right_shoulder_idx)]
        if len(troughs_between) < 2: return None
        
        trough1_idx, trough2_idx = troughs_between[-2:] # Get the two most recent troughs between shoulders
        
        # Calculate the neckline as a line between the two troughs
        x1, y1 = trough1_idx, data['Low'].iloc[trough1_idx]
        x2, y2 = trough2_idx, data['Low'].iloc[trough2_idx]
        slope = (y2 - y1) / (x2 - x1) if (x2 - x1) != 0 else 0
        intercept = y1 - slope * x1
        
        # Check for a decisive breakout below the neckline on the most recent bar
        latest_bar_index = len(data) - 1
        neckline_price_at_breakout = slope * latest_bar_index + intercept
        latest_close = data['Close'].iloc[-1]

        if latest_close < neckline_price_at_breakout:
            pattern_height = head_price - ((y1 + y2) / 2) # Avg height from head to neckline
            
            return {
                'pattern_name': 'Head and Shoulders Top',
                'breakout_price': neckline_price_at_breakout,
                'breakout_direction': 'down',
                'initial_stop_loss': right_shoulder_price, # Stop placed above the right shoulder
                'calculated_price_target': neckline_price_at_breakout - pattern_height,
                'pattern_top_boundary': head_price,
                'pattern_bottom_boundary': neckline_price_at_breakout
            }
        return None

    def detect_ascending_triangle(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Detects an Ascending Triangle with precision.
        This is a bullish continuation pattern.
        """
        if len(data) < 30: return None

        recent_data = data.iloc[-30:] # Analyze the last 30 bars
        
        highs = recent_data['High']
        lows = recent_data['Low']
        
        # Rule 1: Find a flat resistance line (multiple highs at a similar level)
        resistance_level = highs.iloc[-20:-1].max() # Look for resistance before the breakout
        touches_resistance = highs[abs(highs - resistance_level) < (resistance_level * 0.015)].count()
        if touches_resistance < 2: return None

        # Rule 2: Find a rising support line (a series of higher lows)
        recent_lows = lows.iloc[-20:-1]
        # Use linear regression to confirm the upward slope of support
        x = np.arange(len(recent_lows))
        slope, _ = np.polyfit(x, recent_lows, 1)
        if slope <= 0: return None # Slope must be positive

        # Rule 3: Check for a decisive breakout on the latest bar
        latest_close = recent_data['Close'].iloc[-1]
        if latest_close > resistance_level:
            pattern_low = recent_lows.min()
            pattern_height = resistance_level - pattern_low
            
            return {
                'pattern_name': 'Ascending Triangle',
                'breakout_price': resistance_level,
                'breakout_direction': 'up',
                'initial_stop_loss': resistance_level - (pattern_height * 0.5), # Stop inside the pattern
                'calculated_price_target': resistance_level + pattern_height,
                'pattern_top_boundary': resistance_level,
                'pattern_bottom_boundary': pattern_low # This is a simplification
            }
        return None

    # --- Add other fully implemented pattern detection functions here ---
    # e.g., detect_inverse_head_and_shoulders, detect_double_bottom, etc.

# Example Usage
if __name__ == '__main__':
    # This block allows for independent testing of this module.
    # A developer would create sample dataframes here to test each pattern function.
    print("Pattern Detector Module Initialized. Ready for testing.")
