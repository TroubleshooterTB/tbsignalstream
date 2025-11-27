# ==============================================================================
# Arcane Nexus - Live Tactical Alert Engine
# Checklist Module: Macro Checker (macro_checker.py) - vX Grandmaster Edition
#
# This module contains the logic for the first 8 checks of the 30-Point
# "Grandmaster" Checklist. It provides the high-level, strategic filter,
# ensuring the bot only trades in alignment with the broad market context.
# ==============================================================================

import pandas as pd
from typing import Dict, Any, Tuple

# Import fundamental data fetcher
try:
    from trading.data.fundamental_fetcher import get_fundamental_fetcher
    FUNDAMENTALS_AVAILABLE = True
except ImportError:
    FUNDAMENTALS_AVAILABLE = False

class MacroChecker:
    """
    Performs Phase A of the Grandmaster Checklist: Strategic & Macro Environment Filter.
    """

    def __init__(self):
        """Initializes the Macro Checker."""
        self.fundamental_fetcher = None
        if FUNDAMENTALS_AVAILABLE:
            try:
                self.fundamental_fetcher = get_fundamental_fetcher()
            except Exception as e:
                print(f"Warning: Could not initialize fundamental fetcher: {e}")
        
    # ========================================================================
    # Methods called by ExecutionManager (check_1, check_2, etc.)
    # ========================================================================
    
    def check_1_overall_market_trend(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """Check 1: Overall market trend alignment"""
        # Simplified: Check if price above 50 SMA
        if 'sma_50' in data.columns and len(data) > 50:
            return float(data['close'].iloc[-1]) > float(data['sma_50'].iloc[-1])
        return True  # Pass if no data
    
    def check_2_sector_strength(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """
        Check 2: Sector strength confirmation
        Uses relative strength vs market (stock performance vs index)
        """
        try:
            # Calculate 20-day performance for relative strength
            if len(data) < 20:
                return True  # Not enough data
            
            # Stock performance over last 20 days
            stock_perf = (data['close'].iloc[-1] / data['close'].iloc[-20] - 1) * 100
            
            # If stock is significantly outperforming (for longs) or underperforming (for shorts)
            direction = pattern_details.get('direction', 'up')
            
            if direction == 'up':
                # For long trades, stock should be showing relative strength
                # At minimum, should be positive or not severely lagging
                if stock_perf < -5.0:  # More than 5% down in 20 days
                    print(f"❌ Check 2: Weak sector/stock strength ({stock_perf:.1f}% performance)")
                    return False
            else:
                # For short trades, stock should be showing relative weakness
                if stock_perf > 5.0:  # More than 5% up in 20 days
                    print(f"❌ Check 2: Strong sector/stock (not weak enough for short: {stock_perf:.1f}%)")
                    return False
            
            print(f"✅ Check 2: Sector/stock strength OK ({stock_perf:.1f}% 20-day performance)")
            return True
            
        except Exception as e:
            print(f"Check 2 error: {e}")
            return True  # Pass on error
    
    def check_3_economic_calendar_impact(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """
        Check 3: Fundamental strength & economic calendar impact.
        NOW USES REAL FUNDAMENTAL DATA!
        """
        if not self.fundamental_fetcher:
            return True  # Pass if fetcher unavailable
        
        try:
            # Extract symbol from pattern_details or data
            symbol = pattern_details.get('symbol', '')
            if not symbol and hasattr(data, 'name'):
                symbol = data.name
            
            if not symbol:
                return True  # Can't check without symbol
            
            # Fetch fundamentals
            fundamentals = self.fundamental_fetcher.get_fundamentals(symbol)
            
            if not fundamentals:
                return True  # Pass if data unavailable
            
            # Check if fundamentally strong
            is_strong = fundamentals.get('is_fundamentally_strong', True)
            reason = fundamentals.get('reason', 'Unknown')
            
            if not is_strong:
                print(f"❌ Check 3 FAILED: {symbol} - {reason}")
                return False
            
            print(f"✅ Check 3 PASSED: {symbol} - {reason}")
            print(f"   PE: {fundamentals.get('pe_ratio', 0):.1f}, "
                  f"D/E: {fundamentals.get('debt_to_equity', 0):.2f}, "
                  f"ROE: {fundamentals.get('roe', 0):.1f}%")
            
            return True
            
        except Exception as e:
            print(f"Error in fundamental check: {e}")
            return True  # Pass on error (don't block trades)
    
    def check_4_intermarket_analysis(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """
        Check 4: Intermarket analysis confirmation (Catalyst/News awareness)
        Uses price action and volume as proxy for news impact
        """
        try:
            if len(data) < 5:
                return True
            
            # Check for unusual volume spike (proxy for news catalyst)
            recent_avg_volume = data['volume'].iloc[-10:-1].mean() if len(data) >= 10 else data['volume'].mean()
            current_volume = data['volume'].iloc[-1]
            
            volume_ratio = current_volume / recent_avg_volume if recent_avg_volume > 0 else 1.0
            
            # Check for unusual price movement (gap or large candle)
            current_range = abs(data['close'].iloc[-1] - data['open'].iloc[-1])
            avg_range = abs(data['close'] - data['open']).tail(10).mean()
            range_ratio = current_range / avg_range if avg_range > 0 else 1.0
            
            # If both volume and price action are elevated, likely news-driven (good)
            # If neither is elevated, likely technical only (still OK)
            # If price spiked without volume, likely trap (bad)
            
            if range_ratio > 2.0 and volume_ratio < 0.8:
                # Large price move without volume support - suspicious
                print(f"❌ Check 4: Large move without volume (possible trap)")
                return False
            
            print(f"✅ Check 4: Price/volume relationship OK (vol: {volume_ratio:.1f}x, range: {range_ratio:.1f}x)")
            return True
            
        except Exception as e:
            print(f"Check 4 error: {e}")
            return True
    
    def check_5_geopolitical_events(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """
        Check 5: Geopolitical events assessment
        Uses market-wide volatility as proxy for geopolitical risk
        """
        try:
            # Check for extreme volatility that might indicate geopolitical events
            if 'atr' not in data.columns or len(data) < 14:
                return True
            
            current_atr = data['atr'].iloc[-1]
            price = data['close'].iloc[-1]
            atr_pct = (current_atr / price) * 100
            
            # Check historical ATR to see if volatility is spiking
            avg_atr = data['atr'].tail(50).mean() if len(data) >= 50 else current_atr
            atr_spike = current_atr / avg_atr if avg_atr > 0 else 1.0
            
            # If ATR is more than 2x normal, likely elevated geopolitical risk
            if atr_spike > 2.5:
                print(f"❌ Check 5: Extreme volatility detected (ATR {atr_spike:.1f}x normal) - possible geopolitical risk")
                return False
            
            # Also check if we're in extreme high volatility regime
            if atr_pct > 8.0:  # More than 8% daily range
                print(f"❌ Check 5: Very high ATR ({atr_pct:.1f}%) - unstable environment")
                return False
            
            print(f"✅ Check 5: Volatility acceptable (ATR: {atr_pct:.1f}%, spike: {atr_spike:.1f}x)")
            return True
            
        except Exception as e:
            print(f"Check 5 error: {e}")
            return True
    
    def check_6_liquidity_conditions(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """Check 6: Liquidity conditions assessment"""
        # Simple check: Ensure volume is present
        if 'volume' in data.columns:
            return data['volume'].iloc[-1] > 0
        return True
    
    def check_7_volatility_regime(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """Check 7: Volatility regime confirmation"""
        # Simple check: Ensure ATR exists (not too volatile)
        if 'atr' in data.columns:
            atr = data['atr'].iloc[-1]
            price = data['close'].iloc[-1]
            atr_pct = (atr / price) * 100
            # Reject if ATR > 5% (extreme volatility)
            return atr_pct < 5.0
        return True
    
    def check_8_major_news_announcements(self, data: pd.DataFrame, pattern_details: Dict[str, Any]) -> bool:
        """
        Check 8: Major news announcements check
        Detects unusual market behavior that suggests major news
        """
        try:
            if len(data) < 3:
                return True
            
            # Check for gap opening (possible overnight news)
            prev_close = data['close'].iloc[-2]
            current_open = data['open'].iloc[-1]
            gap_pct = abs((current_open - prev_close) / prev_close) * 100
            
            # Check for unusual intraday volatility
            current_range = data['high'].iloc[-1] - data['low'].iloc[-1]
            current_price = data['close'].iloc[-1]
            range_pct = (current_range / current_price) * 100
            
            # Large gap might indicate earnings or major news
            if gap_pct > 3.0:
                print(f"❌ Check 8: Large gap detected ({gap_pct:.1f}%) - possible major news event")
                return False
            
            # Extreme intraday range might indicate ongoing news
            if range_pct > 5.0:
                print(f"❌ Check 8: Extreme intraday range ({range_pct:.1f}%) - possible major news")
                return False
            
            print(f"✅ Check 8: No major news indicators (gap: {gap_pct:.1f}%, range: {range_pct:.1f}%)")
            return True
            
        except Exception as e:
            print(f"Check 8 error: {e}")
            return True
    
    # ========================================================================
    # Original run_all_checks methods (for backward compatibility)
    # ========================================================================

    def run_all_checks(self, stock_data: pd.DataFrame, nifty_data: pd.DataFrame, sector_data: pd.DataFrame, sentiment_context: Dict[str, Any], direction: str) -> Tuple[bool, str]:
        """
        Runs all 8 macro checks sequentially.

        Returns:
            A tuple of (bool, str): (True if all checks pass, "Reason for failure or success").
        """
        checks = [
            self._check_01_market_health,
            self._check_02_sector_dominance,
            self._check_03_fundamental_strength,
            self._check_04_catalyst_narrative,
            self._check_05_sentiment_phase,
            self._check_06_contrarian_check,
            self._check_07_wall_of_worry,
            self._check_08_slope_of_hope,
        ]

        for check_function in checks:
            # In a real implementation, more context would be passed to each function as needed
            is_passed, reason = check_function(nifty_data, sector_data, sentiment_context, direction)
            if not is_passed:
                return False, reason # Fails fast on the first failed check
        
        return True, "All Macro Checks Passed."

    # --- Individual Checklist Functions ---

    def _check_01_market_health(self, nifty_data: pd.DataFrame, _, __, direction: str) -> Tuple[bool, str]:
        """Check 1: Is the NIFTY 50 above its 200-day moving average for longs?"""
        if len(nifty_data) < 200: return False, "Not enough NIFTY data for 200 DMA."
        
        nifty_200_dma = nifty_data['Close'].rolling(window=200).mean().iloc[-1]
        latest_nifty_close = nifty_data['Close'].iloc[-1]

        if direction == 'up' and latest_nifty_close < nifty_200_dma:
            return False, "Check 1 FAILED: Market Health is bearish (NIFTY below 200 DMA)."
        if direction == 'down' and latest_nifty_close > nifty_200_dma:
            return False, "Check 1 FAILED: Market Health is bullish (NIFTY above 200 DMA)."
        return True, "Check 1 PASSED: Market Health."

    def _check_02_sector_dominance(self, nifty_data: pd.DataFrame, sector_data: pd.DataFrame, _, direction: str) -> Tuple[bool, str]:
        """Check 2: Is the stock's sector outperforming the NIFTY 50?"""
        if len(nifty_data) < 20 or len(sector_data) < 20: return False, "Not enough data for performance check."
        
        nifty_perf = (nifty_data['Close'].iloc[-1] / nifty_data['Close'].iloc[-20]) - 1 # 1-month performance
        sector_perf = (sector_data['Close'].iloc[-1] / sector_data['Close'].iloc[-20]) - 1

        if direction == 'up' and sector_perf < nifty_perf:
            return False, "Check 2 FAILED: Sector is underperforming the NIFTY."
        if direction == 'down' and sector_perf > nifty_perf:
            return False, "Check 2 FAILED: Sector is outperforming the NIFTY."
        return True, "Check 2 PASSED: Sector Dominance."

    def _check_03_fundamental_strength(self, *args) -> Tuple[bool, str]:
        """Check 3: Does the company have a solid balance sheet? (Placeholder)"""
        # In a real system, this would query a fundamental data source.
        # For now, we assume this check passes for liquid, well-known stocks.
        return True, "Check 3 PASSED: Fundamental Strength (Assumed)."

    def _check_04_catalyst_narrative(self, _, __, sentiment_context: Dict[str, Any], direction: str) -> Tuple[bool, str]:
        """Check 4: Is there a powerful, ongoing news story?"""
        if not sentiment_context.get('has_recent_news', True): # Default to True for testing
            return False, "Check 4 FAILED: No recent significant news catalyst."
        return True, "Check 4 PASSED: Catalyst Narrative."

    def _check_05_sentiment_phase(self, _, __, sentiment_context: Dict[str, Any], direction: str) -> Tuple[bool, str]:
        """Check 5: Is the trade in the 'rumor' phase, not the 'fact' phase?"""
        if sentiment_context.get('phase') == 'sell_the_fact':
            return False, "Check 5 FAILED: Narrative is in the 'sell the fact' stage."
        return True, "Check 5 PASSED: Sentiment Phase."

    def _check_06_contrarian_check(self, *args) -> Tuple[bool, str]:
        """Check 6: Is this a contrarian 'blood in the street' opportunity? (Context-dependent)"""
        # This check is specific and would only pass in rare panic scenarios.
        # By default, for a normal trend trade, this check is neutral and passes.
        return True, "Check 6 PASSED: Contrarian Check (Neutral)."

    def _check_07_wall_of_worry(self, _, __, sentiment_context: Dict[str, Any], direction: str) -> Tuple[bool, str]:
        """Check 7: Is there healthy skepticism, or dangerous euphoria?"""
        if direction == 'up' and sentiment_context.get('sentiment_score', 0) > 0.9:
            return False, "Check 7 FAILED: 'Wall of Worry' check failed due to market euphoria."
        return True, "Check 7 PASSED: 'Wall of Worry'."

    def _check_08_slope_of_hope(self, _, __, sentiment_context: Dict[str, Any], direction: str) -> Tuple[bool, str]:
        """Check 8: Is this a weak 'slope of hope' rally to be sold into?"""
        # This check is primarily for confirming short trades.
        if direction == 'down' and not sentiment_context.get('is_weak_rally', False):
            # If we are looking for a short, but the rally is strong, this check fails.
            return False, "Check 8 FAILED: Rally appears strong, not a 'Slope of Hope'."
        return True, "Check 8 PASSED: 'Slope of Hope'."

if __name__ == '__main__':
    # This block is for independent testing of this module.
    print("Macro Checker Module Initialized. Ready for testing.")
