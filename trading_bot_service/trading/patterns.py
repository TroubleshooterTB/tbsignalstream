# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Expert Module: Pattern Detector (patterns.py)
#
# This module contains the deep knowledge for identifying classic and advanced
# technical analysis chart patterns. It uses robust methods like peak/trough
# detection and linear regression for objective analysis.
# ==============================================================================

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from scipy.signal import find_peaks

class PatternDetector:
    """
    Scans market data to identify high-probability chart patterns.
    Each detection function is a specialist for a specific pattern.
    """

    def __init__(self):
        """Initializes the master pattern detector."""
        self.pattern_scanners = [
            self.detect_double_top_bottom,
            self.detect_flags,
            self.detect_triangles_and_wedges,
            # Add other pattern detection functions here as they are built
        ]

    def scan(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Runs all available pattern scanners on the latest market data.

        Args:
            market_data: The DataFrame of price history (OHLCV).

        Returns:
            A dictionary containing the details of the first confirmed pattern found,
            or an empty dictionary if no patterns are confirmed.
        """
        for scanner in self.pattern_scanners:
            pattern_details = scanner(market_data)
            if pattern_details:
                return pattern_details
        return {}

    def _get_swing_points(self, data: pd.Series, distance=10, prominence_factor=None):
        """
        Utility to find swing highs and lows.
        
        Args:
            data: Price series (High or Low)
            distance: Minimum candles between peaks (default 10 for stricter detection)
            prominence_factor: DEPRECATED - not used for intraday detection
        """
        # For intraday 1-minute data, use distance-only detection (no prominence)
        # Increased distance to 10 to reduce false pattern signals
        peaks, _ = find_peaks(data, distance=distance)
        troughs, _ = find_peaks(-data, distance=distance)
        return peaks, troughs

    def detect_double_top_bottom(self, data: pd.DataFrame, lookback=50) -> Dict[str, Any]:
        """Detects Double Top and Double Bottom patterns (both forming and confirmed)."""
        if len(data) < lookback: return {}
        recent_data = data.iloc[-lookback:]

        # Find swing highs and lows separately
        high_peaks, _ = self._get_swing_points(recent_data['High'])
        _, low_troughs = self._get_swing_points(recent_data['Low'])
        
        # Double Top - STRICT CRITERIA TO REDUCE FALSE SIGNALS
        if len(high_peaks) >= 2:
            peak1_idx, peak2_idx = high_peaks[-2], high_peaks[-1]
            
            # MINIMUM PATTERN DURATION: at least 20 candles between peaks
            if peak2_idx - peak1_idx < 20:
                pass  # Skip this pattern, continue to Double Bottom check
            else:
                peak1_price, peak2_price = recent_data['High'].iloc[peak1_idx], recent_data['High'].iloc[peak2_idx]

                # TIGHTER TOLERANCE: Peaks must be within 1% (reduced from 3%)
                if abs(peak1_price - peak2_price) / peak1_price < 0.01:
                    trough_between = recent_data['Low'].iloc[peak1_idx:peak2_idx].min()
                    current_price = data['Close'].iloc[-1]
                    height = peak1_price - trough_between
                    
                    # PATTERN HEIGHT CHECK: Must be at least 1% (increased from 0.5%)
                    height_pct = (height / peak1_price) * 100
                    if height_pct < 1.0:
                        pass  # Skip weak pattern
                    else:
                        # TREND FILTER: Check if in downtrend (price below 20-MA)
                        if len(data) >= 20:
                            ma20 = data['Close'].rolling(20).mean().iloc[-1]
                            if current_price >= ma20:
                                pass  # Not in downtrend, skip
                            else:
                                # CONFIRMED: Strong breakout below support with at least 0.2% confirmation
                                breakout_distance = (trough_between - current_price) / trough_between
                                if breakout_distance >= 0.002:
                                    return {
                                        'pattern_name': 'Double Top', 'breakout_direction': 'down',
                                        'pattern_status': 'confirmed', 'tradeable': True,
                                        'breakout_price': trough_between, 'duration': lookback,
                                        'initial_stop_loss': peak2_price,
                                        'calculated_price_target': trough_between - height,
                                        'pattern_top_boundary': peak1_price, 'pattern_bottom_boundary': trough_between
                                    }
                        # FORMING patterns removed - only trade confirmed breakouts with trend alignment
        
        # Double Bottom - STRICT CRITERIA TO REDUCE FALSE SIGNALS
        if len(low_troughs) >= 2:
            trough1_idx, trough2_idx = low_troughs[-2], low_troughs[-1]
            
            # MINIMUM PATTERN DURATION: at least 20 candles between troughs
            if trough2_idx - trough1_idx < 20:
                return {}  # Skip weak pattern
            
            trough1_price, trough2_price = recent_data['Low'].iloc[trough1_idx], recent_data['Low'].iloc[trough2_idx]

            # TIGHTER TOLERANCE: Troughs must be within 1% (reduced from 3%)
            if abs(trough1_price - trough2_price) / trough1_price < 0.01:
                peak_between = recent_data['High'].iloc[trough1_idx:trough2_idx].max()
                current_price = data['Close'].iloc[-1]
                height = peak_between - trough1_price
                
                # PATTERN HEIGHT CHECK: Must be at least 1% (increased from 0.5%)
                height_pct = (height / trough1_price) * 100
                if height_pct < 1.0:
                    return {}  # Skip weak pattern
                
                # TREND FILTER: Check if in uptrend (price above 20-MA)
                if len(data) >= 20:
                    ma20 = data['Close'].rolling(20).mean().iloc[-1]
                    if current_price <= ma20:
                        return {}  # Not in uptrend, skip
                
                # CONFIRMED: Strong breakout above resistance with at least 0.2% confirmation
                breakout_distance = (current_price - peak_between) / peak_between
                if breakout_distance >= 0.002:
                    return {
                        'pattern_name': 'Double Bottom', 'breakout_direction': 'up',
                        'pattern_status': 'confirmed', 'tradeable': True,
                        'breakout_price': peak_between, 'duration': lookback,
                        'initial_stop_loss': trough2_price,
                        'calculated_price_target': peak_between + height,
                        'pattern_top_boundary': peak_between, 'pattern_bottom_boundary': trough1_price
                    }
                # FORMING patterns removed - only trade confirmed breakouts with trend alignment
        return {}

    def detect_flags(self, data: pd.DataFrame, pole_lookback=15, flag_lookback=20) -> Dict[str, Any]:
        """Detects Bull and Bear Flag patterns."""
        if len(data) < pole_lookback + flag_lookback: return {}
        
        # Pole detection
        pole_data = data.iloc[-(pole_lookback + flag_lookback):-flag_lookback]
        price_change = pole_data['Close'].iloc[-1] - pole_data['Close'].iloc[0]
        pole_height = abs(price_change)
        
        # Flag detection
        flag_data = data.iloc[-flag_lookback:]
        
        # Bull Flag
        if price_change > 0 and pole_height / pole_data['Close'].iloc[0] > 0.04: # At least 4% pole move (relaxed from 8%)
            highs, lows = self._get_swing_points(flag_data['High'], 3, 0.005)
            if len(highs) > 1:
                high_coef = np.polyfit(highs, flag_data['High'].iloc[highs], 1)
                slope = high_coef[0]
                if slope < 0: # Downward consolidation
                    resistance_line = flag_data['High'].iloc[highs[-1]]
                    if data['Close'].iloc[-1] > resistance_line:
                        return {
                            'pattern_name': 'Bull Flag', 'breakout_direction': 'up',
                            'breakout_price': resistance_line, 'duration': flag_lookback,
                            'initial_stop_loss': flag_data['Low'].min(),
                            'calculated_price_target': resistance_line + pole_height,
                            'pattern_top_boundary': resistance_line, 'pattern_bottom_boundary': flag_data['Low'].min()
                        }
        # Bear Flag
        if price_change < 0 and pole_height / pole_data['Close'].iloc[0] > 0.04: # At least 4% pole move (relaxed from 8%)
            highs, lows = self._get_swing_points(flag_data['Low'], 3, 0.005)
            if len(lows) > 1:
                low_coef = np.polyfit(lows, flag_data['Low'].iloc[lows], 1)
                slope = low_coef[0]
                if slope > 0: # Upward consolidation
                    support_line = flag_data['Low'].iloc[lows[-1]]
                    if data['Close'].iloc[-1] < support_line:
                        return {
                            'pattern_name': 'Bear Flag', 'breakout_direction': 'down',
                            'breakout_price': support_line, 'duration': flag_lookback,
                            'initial_stop_loss': flag_data['High'].max(),
                            'calculated_price_target': support_line - pole_height,
                            'pattern_top_boundary': flag_data['High'].max(), 'pattern_bottom_boundary': support_line
                        }
        return {}

    def detect_triangles_and_wedges(self, data: pd.DataFrame, lookback=30) -> Dict[str, Any]:
        """Detects Triangles (Ascending, Descending, Symmetrical) and Wedges (Rising, Falling)."""
        if len(data) < lookback: return {}
        recent_data = data.iloc[-lookback:]

        high_peaks, low_troughs = self._get_swing_points(recent_data['High'], 5, 0.01)
        
        if len(high_peaks) < 2 or len(low_troughs) < 2: return {}
        
        # Fit linear regression to swing points
        high_coef = np.polyfit(high_peaks, recent_data['High'].iloc[high_peaks], 1)
        high_slope, high_intercept = high_coef[0], high_coef[1]
        
        low_coef = np.polyfit(low_troughs, recent_data['Low'].iloc[low_troughs], 1)
        low_slope, low_intercept = low_coef[0], low_coef[1]

        latest_close = data['Close'].iloc[-1]
        resistance_price = high_slope * lookback + high_intercept
        support_price = low_slope * lookback + low_intercept
        pattern_height = resistance_price - support_price

        # Classify and check for breakout
        slope_tolerance = 0.1 * abs(low_slope + high_slope)
        
        # Rising Wedge
        if high_slope > slope_tolerance and low_slope > slope_tolerance and high_slope < low_slope:
            if latest_close < support_price:
                return {'pattern_name': 'Rising Wedge', 'breakout_direction': 'down', 'breakout_price': support_price, 'duration': lookback, 'initial_stop_loss': resistance_price, 'calculated_price_target': support_price - pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}
        
        # Falling Wedge
        if high_slope < -slope_tolerance and low_slope < -slope_tolerance and high_slope < low_slope:
            if latest_close > resistance_price:
                return {'pattern_name': 'Falling Wedge', 'breakout_direction': 'up', 'breakout_price': resistance_price, 'duration': lookback, 'initial_stop_loss': support_price, 'calculated_price_target': resistance_price + pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}

        # Ascending Triangle
        if abs(high_slope) < slope_tolerance and low_slope > slope_tolerance:
            if latest_close > resistance_price:
                return {'pattern_name': 'Ascending Triangle', 'breakout_direction': 'up', 'breakout_price': resistance_price, 'duration': lookback, 'initial_stop_loss': support_price, 'calculated_price_target': resistance_price + pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}

        # Descending Triangle
        if high_slope < -slope_tolerance and abs(low_slope) < slope_tolerance:
            if latest_close < support_price:
                return {'pattern_name': 'Descending Triangle', 'breakout_direction': 'down', 'breakout_price': support_price, 'duration': lookback, 'initial_stop_loss': resistance_price, 'calculated_price_target': support_price - pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}

        # Symmetrical Triangle
        if high_slope < -slope_tolerance and low_slope > slope_tolerance:
            if latest_close > resistance_price: # Upward breakout
                return {'pattern_name': 'Symmetrical Triangle', 'breakout_direction': 'up', 'breakout_price': resistance_price, 'duration': lookback, 'initial_stop_loss': support_price, 'calculated_price_target': resistance_price + pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}
            if latest_close < support_price: # Downward breakout
                return {'pattern_name': 'Symmetrical Triangle', 'breakout_direction': 'down', 'breakout_price': support_price, 'duration': lookback, 'initial_stop_loss': resistance_price, 'calculated_price_target': support_price - pattern_height, 'pattern_top_boundary': resistance_price, 'pattern_bottom_boundary': support_price}
                
        return {}
