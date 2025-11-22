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

class MacroChecker:
    """
    Performs Phase A of the Grandmaster Checklist: Strategic & Macro Environment Filter.
    """

    def __init__(self):
        """Initializes the Macro Checker."""
        pass

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
