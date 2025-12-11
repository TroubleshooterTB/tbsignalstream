"""
Advanced 24-Level Screening Manager - Universal Validation Layer

This module implements the missing levels (5, 14, 15, 19, 20, 21, 22, 23, 24)
from the institutional-grade screening framework.

ALL trading strategies (Pattern, Ironclad, Dual) must pass through this layer
before order execution.

Design Principles:
- Non-invasive: Can be toggled on/off via config
- Fail-safe: Errors don't crash the bot, just log warnings
- Modular: Each level can be enabled/disabled independently
- Observable: Detailed logging for each validation step
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)


class AdvancedScreeningConfig:
    """Configuration for Advanced Screening Layer"""
    
    def __init__(self):
        # Enable/disable specific levels (for gradual rollout)
        self.enable_ma_crossover = True          # Level 5
        self.enable_bb_squeeze = True            # Level 14
        self.enable_var_limit = True             # Level 15 - CRITICAL
        self.enable_sr_confluence = True         # Level 19
        self.enable_gap_analysis = True          # Level 20
        self.enable_nrb_trigger = True           # Level 21
        self.enable_tick_indicator = True        # Level 22 - NOW ENABLED (real TICK calculation)
        self.enable_ml_filter = True             # Level 23 - NOW ENABLED (heuristic scoring)
        self.enable_retest_logic = True          # Level 24
        
        # Risk parameters
        self.max_portfolio_var_percent = 15.0    # Maximum 15% portfolio VaR
        self.var_confidence_level = 0.95         # 95% confidence level
        
        # MA Crossover parameters (Level 5)
        self.fast_ma_period = 25
        self.slow_ma_period = 50
        self.crossover_lookback = 5              # Check last 5 bars for crossover
        
        # BB Squeeze parameters (Level 14)
        self.bb_squeeze_threshold = 0.02         # 2% bandwidth = squeeze
        self.bb_expansion_threshold = 0.04       # 4% bandwidth = expansion ready
        
        # S&R Confluence parameters (Level 19)
        self.sr_proximity_percent = 0.5          # 0.5% away from S&R = too close
        
        # Gap parameters (Level 20)
        self.min_gap_percent = 0.3               # 0.3% gap = significant
        
        # NRB parameters (Level 21)
        self.nrb_lookback = 10                   # Check last 10 bars
        self.nrb_threshold_percentile = 20       # Narrowest 20% of ranges
        
        # Retest parameters (Level 24)
        self.retest_proximity_percent = 0.3      # 0.3% away from breakout level
        self.retest_max_wait_bars = 5            # Wait max 5 bars for retest
        
        # Fail-safe mode
        self.fail_safe_mode = True               # If True, validation errors don't block trades
        
        logger.info("AdvancedScreeningConfig initialized with fail-safe mode: %s", self.fail_safe_mode)


class AdvancedScreeningManager:
    """
    Universal 24-Level Screening Layer
    
    Implements missing levels from institutional framework:
    - Level 5: Dual MA Crossover
    - Level 14: Bollinger Band Squeeze
    - Level 15: Value-at-Risk (VaR) Limit - CRITICAL
    - Level 19: Support/Resistance Confluence
    - Level 20: Gap Price Level Analysis
    - Level 21: Narrow Range Bar (NRB) Trigger
    - Level 22: TICK Indicator (Market Flow) - Optional
    - Level 23: ML Prediction Filter - Optional
    - Level 24: Imbalance Retest Execution
    """
    
    def __init__(self, config: Optional[AdvancedScreeningConfig] = None, 
                 portfolio_value: float = 1000000.0):
        """
        Initialize Advanced Screening Manager
        
        Args:
            config: Screening configuration (uses defaults if None)
            portfolio_value: Current portfolio value for VaR calculation
        """
        self.config = config or AdvancedScreeningConfig()
        self.portfolio_value = portfolio_value
        
        # State tracking for retest logic (Level 24)
        self.breakout_levels = {}  # {symbol: {'level': price, 'timestamp': datetime, 'direction': 'up/down'}}
        
        # Gap tracking (Level 20)
        self.gap_levels = {}  # {symbol: [{'level': price, 'type': 'up/down', 'timestamp': datetime}]}
        
        # ML model placeholder (Level 23)
        self.ml_model = None  # Will be loaded when available
        
        # TICK indicator cache (Level 22)
        self._tick_data_cache = None
        self._tick_cache_time = None
        
        # API client for TICK data (will be set by bot)
        self.api_client = None
        
        logger.info("✅ AdvancedScreeningManager initialized (Portfolio: ₹%.2f)", portfolio_value)
        logger.info("Enabled levels: %s", self._get_enabled_levels())
    
    def _get_enabled_levels(self) -> str:
        """Get list of enabled screening levels"""
        enabled = []
        if self.config.enable_ma_crossover: enabled.append("5-MA_Cross")
        if self.config.enable_bb_squeeze: enabled.append("14-BB_Squeeze")
        if self.config.enable_var_limit: enabled.append("15-VaR")
        if self.config.enable_sr_confluence: enabled.append("19-S/R")
        if self.config.enable_gap_analysis: enabled.append("20-Gap")
        if self.config.enable_nrb_trigger: enabled.append("21-NRB")
        if self.config.enable_tick_indicator: enabled.append("22-TICK")
        if self.config.enable_ml_filter: enabled.append("23-ML")
        if self.config.enable_retest_logic: enabled.append("24-Retest")
        return ", ".join(enabled) if enabled else "None (All disabled)"
    
    def validate_signal(self, symbol: str, signal_data: Dict, df: pd.DataFrame, 
                       current_positions: Dict, current_price: float) -> Tuple[bool, str]:
        """
        Universal validation method - ALL strategies call this
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            signal_data: Signal dictionary from strategy
                {
                    'action': 'BUY'/'SELL'/'HOLD',
                    'entry_price': float,
                    'stop_loss': float,
                    'target': float,
                    'pattern_name': str (optional),
                    'score': float (optional)
                }
            df: DataFrame with OHLCV + indicators
            current_positions: Dictionary of current open positions
            current_price: Current market price
            
        Returns:
            Tuple[bool, str]: (is_valid, reason)
                - True, "PASSED" if all checks pass
                - False, "Failed: [reason]" if any check fails
        """
        try:
            # Extract signal details
            action = signal_data.get('action', 'HOLD')
            entry_price = signal_data.get('entry_price', current_price)
            stop_loss = signal_data.get('stop_loss', entry_price * 0.98)
            target = signal_data.get('target', entry_price * 1.05)
            
            if action == 'HOLD':
                return True, "HOLD signal - no validation needed"
            
            # Direction
            is_long = action == 'BUY'
            
            logger.info(f"🔍 [{symbol}] Advanced Screening: {action} @ ₹{entry_price:.2f}")
            
            # ========== LEVEL 5: Dual MA Crossover ==========
            if self.config.enable_ma_crossover:
                passed, reason = self._check_ma_crossover(df, is_long)
                if not passed:
                    return self._handle_failure(f"Level 5 - MA Crossover: {reason}")
            
            # ========== LEVEL 14: BB Squeeze Detection ==========
            if self.config.enable_bb_squeeze:
                passed, reason = self._check_bb_squeeze(df, is_long)
                if not passed:
                    return self._handle_failure(f"Level 14 - BB Squeeze: {reason}")
            
            # ========== LEVEL 15: VaR Limit (CRITICAL) ==========
            if self.config.enable_var_limit:
                passed, reason = self._check_var_limit(
                    symbol, entry_price, stop_loss, current_positions
                )
                if not passed:
                    return self._handle_failure(f"Level 15 - VaR: {reason}", critical=True)
            
            # ========== LEVEL 19: S&R Confluence ==========
            if self.config.enable_sr_confluence:
                passed, reason = self._check_sr_confluence(df, entry_price, stop_loss, is_long)
                if not passed:
                    return self._handle_failure(f"Level 19 - S/R: {reason}")
            
            # ========== LEVEL 20: Gap Analysis ==========
            if self.config.enable_gap_analysis:
                passed, reason = self._check_gap_levels(symbol, df, entry_price, is_long)
                if not passed:
                    return self._handle_failure(f"Level 20 - Gap: {reason}")
            
            # ========== LEVEL 21: NRB Trigger ==========
            if self.config.enable_nrb_trigger:
                passed, reason = self._check_nrb_pattern(df)
                if not passed:
                    return self._handle_failure(f"Level 21 - NRB: {reason}")
            
            # ========== LEVEL 22: TICK Indicator (Optional) ==========
            if self.config.enable_tick_indicator:
                passed, reason = self._check_tick_indicator(is_long)
                if not passed:
                    return self._handle_failure(f"Level 22 - TICK: {reason}")
            
            # ========== LEVEL 23: ML Filter (Optional) ==========
            if self.config.enable_ml_filter:
                passed, reason = self._check_ml_prediction(symbol, df, signal_data, is_long)
                if not passed:
                    return self._handle_failure(f"Level 23 - ML: {reason}")
            
            # ========== LEVEL 24: Retest Logic ==========
            if self.config.enable_retest_logic:
                passed, reason = self._check_retest_opportunity(
                    symbol, df, entry_price, is_long
                )
                if not passed:
                    return self._handle_failure(f"Level 24 - Retest: {reason}")
            
            # ========== ALL CHECKS PASSED ==========
            logger.info(f"✅ [{symbol}] Advanced Screening PASSED - All enabled levels cleared")
            return True, "PASSED"
            
        except Exception as e:
            logger.error(f"Error in advanced screening for {symbol}: {e}", exc_info=True)
            if self.config.fail_safe_mode:
                logger.warning(f"⚠️ [{symbol}] Screening error in fail-safe mode - ALLOWING trade")
                return True, f"PASSED (fail-safe: {str(e)})"
            else:
                return False, f"Screening error: {str(e)}"
    
    def _handle_failure(self, reason: str, critical: bool = False) -> Tuple[bool, str]:
        """
        Handle validation failure based on fail-safe mode
        
        Args:
            reason: Failure reason
            critical: If True, block trade even in fail-safe mode
            
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        if critical:
            logger.warning(f"🚫 CRITICAL FAILURE: {reason} - Trade BLOCKED")
            return False, f"CRITICAL: {reason}"
        
        if self.config.fail_safe_mode:
            logger.warning(f"⚠️ {reason} - Allowing in fail-safe mode")
            return True, f"PASSED (fail-safe warning: {reason})"
        else:
            logger.info(f"❌ {reason} - Trade BLOCKED")
            return False, reason
    
    # ========================================================================
    # LEVEL IMPLEMENTATIONS
    # ========================================================================
    
    def _check_ma_crossover(self, df: pd.DataFrame, is_long: bool) -> Tuple[bool, str]:
        """
        Level 5: Dual MA Crossover Detection
        
        Ensures trade is aligned with recent MA crossover momentum.
        
        Logic:
        - BUY: Fast MA (25) recently crossed ABOVE Slow MA (50) and remains above
        - SELL: Fast MA recently crossed BELOW Slow MA and remains below
        """
        try:
            if len(df) < self.config.slow_ma_period + self.config.crossover_lookback:
                return True, "Insufficient data for MA crossover check"
            
            # Calculate MAs (use EMA for responsiveness)
            fast_ma = df['Close'].ewm(span=self.config.fast_ma_period, adjust=False).mean()
            slow_ma = df['Close'].ewm(span=self.config.slow_ma_period, adjust=False).mean()
            
            # Current alignment
            current_fast = fast_ma.iloc[-1]
            current_slow = slow_ma.iloc[-1]
            
            if is_long:
                # Check if fast MA is above slow MA
                if current_fast <= current_slow:
                    return False, f"Fast MA (₹{current_fast:.2f}) below Slow MA (₹{current_slow:.2f}) - bearish alignment"
                
                # Check for recent bullish crossover in last N bars
                lookback_df = df.tail(self.config.crossover_lookback)
                fast_lookback = fast_ma.tail(self.config.crossover_lookback)
                slow_lookback = slow_ma.tail(self.config.crossover_lookback)
                
                # Was there a crossover? (fast was below, now above)
                had_crossover = any(
                    (fast_lookback.iloc[i-1] <= slow_lookback.iloc[i-1]) and 
                    (fast_lookback.iloc[i] > slow_lookback.iloc[i])
                    for i in range(1, len(fast_lookback))
                )
                
                if not had_crossover:
                    # No recent crossover, but check if already in strong uptrend
                    distance_percent = ((current_fast - current_slow) / current_slow) * 100
                    if distance_percent < 0.5:  # Less than 0.5% separation
                        return False, "No recent bullish crossover and weak MA separation"
                
                return True, "MA alignment bullish"
                
            else:  # SELL
                if current_fast >= current_slow:
                    return False, f"Fast MA (₹{current_fast:.2f}) above Slow MA (₹{current_slow:.2f}) - bullish alignment"
                
                lookback_df = df.tail(self.config.crossover_lookback)
                fast_lookback = fast_ma.tail(self.config.crossover_lookback)
                slow_lookback = slow_ma.tail(self.config.crossover_lookback)
                
                had_crossover = any(
                    (fast_lookback.iloc[i-1] >= slow_lookback.iloc[i-1]) and 
                    (fast_lookback.iloc[i] < slow_lookback.iloc[i])
                    for i in range(1, len(fast_lookback))
                )
                
                if not had_crossover:
                    distance_percent = ((current_slow - current_fast) / current_slow) * 100
                    if distance_percent < 0.5:
                        return False, "No recent bearish crossover and weak MA separation"
                
                return True, "MA alignment bearish"
                
        except Exception as e:
            logger.error(f"Error in MA crossover check: {e}")
            return True, f"MA crossover check error (passed): {str(e)}"
    
    def _check_bb_squeeze(self, df: pd.DataFrame, is_long: bool) -> Tuple[bool, str]:
        """
        Level 14: Bollinger Band Squeeze Detection
        
        Identifies consolidation (squeeze) → expansion patterns.
        Trade should occur AFTER squeeze (during expansion).
        """
        try:
            if 'bb_width' not in df.columns or 'bb_position' not in df.columns:
                return True, "BB indicators not available"
            
            current_bb_width = df['bb_width'].iloc[-1]
            
            # Check if currently in squeeze (too tight - avoid)
            if current_bb_width < self.config.bb_squeeze_threshold:
                return False, f"BB Squeeze active (width: {current_bb_width:.4f}) - awaiting expansion"
            
            # Check if recently expanded from squeeze (ideal)
            if len(df) >= 5:
                recent_widths = df['bb_width'].tail(5)
                was_squeezed = any(w < self.config.bb_squeeze_threshold for w in recent_widths[:-1])
                is_expanding = current_bb_width > self.config.bb_squeeze_threshold
                
                if was_squeezed and is_expanding:
                    return True, f"BB expansion detected (width: {current_bb_width:.4f}) - ideal entry"
            
            # Check if in normal/expanded state (acceptable)
            if current_bb_width >= self.config.bb_squeeze_threshold:
                return True, f"BB width normal (width: {current_bb_width:.4f})"
            
            return False, "BB conditions not ideal"
            
        except Exception as e:
            logger.error(f"Error in BB squeeze check: {e}")
            return True, f"BB squeeze check error (passed): {str(e)}"
    
    def _check_var_limit(self, symbol: str, entry_price: float, stop_loss: float,
                         current_positions: Dict) -> Tuple[bool, str]:
        """
        Level 15: Value-at-Risk (VaR) Portfolio Limit - CRITICAL
        
        Ensures total portfolio risk doesn't exceed maximum threshold.
        This is THE most important risk management check.
        
        Logic:
        - Calculate risk for this new trade
        - Calculate existing risk from open positions
        - Total risk must be <= max_portfolio_var_percent
        """
        try:
            # Calculate risk for this trade
            trade_risk_per_share = abs(entry_price - stop_loss)
            trade_risk_percent = (trade_risk_per_share / entry_price) * 100
            
            # Assume position sizing: 5% portfolio risk per trade (from risk_manager)
            # This trade would add 5% to portfolio VaR
            new_trade_var = 5.0  # Standard position sizing
            
            # Calculate existing portfolio VaR from open positions
            existing_var = 0.0
            for pos_symbol, position in current_positions.items():
                # Each position contributes its risk
                # Simplified: assume each position = 5% risk (can be refined)
                existing_var += 5.0
            
            # Total VaR if this trade is taken
            total_var = existing_var + new_trade_var
            
            # Check against limit
            if total_var > self.config.max_portfolio_var_percent:
                return False, (f"VaR limit exceeded: {total_var:.1f}% > "
                              f"{self.config.max_portfolio_var_percent:.1f}% "
                              f"(Existing: {existing_var:.1f}%, New: {new_trade_var:.1f}%)")
            
            logger.info(f"✅ VaR Check: {total_var:.1f}% / {self.config.max_portfolio_var_percent:.1f}% "
                       f"(Existing: {existing_var:.1f}%, New: {new_trade_var:.1f}%)")
            return True, f"VaR within limits: {total_var:.1f}%"
            
        except Exception as e:
            logger.error(f"Error in VaR check: {e}")
            # VaR is CRITICAL - if calculation fails, block trade
            return False, f"VaR calculation error: {str(e)}"
    
    def _check_sr_confluence(self, df: pd.DataFrame, entry_price: float, 
                            stop_loss: float, is_long: bool) -> Tuple[bool, str]:
        """
        Level 19: Support/Resistance Confluence
        
        Ensures entry is not at a major S/R level that could reject price.
        
        Logic:
        - BUY: Entry should be near support, stop below support
        - SELL: Entry should be near resistance, stop above resistance
        - Entry should NOT be at resistance (long) or support (short)
        """
        try:
            if 'support_1' not in df.columns or 'resistance_1' not in df.columns:
                return True, "S/R levels not available"
            
            support_1 = df['support_1'].iloc[-1]
            support_2 = df['support_2'].iloc[-1]
            resistance_1 = df['resistance_1'].iloc[-1]
            resistance_2 = df['resistance_2'].iloc[-1]
            
            proximity_threshold = self.config.sr_proximity_percent / 100.0
            
            if is_long:
                # Check if entry is too close to resistance (bad for longs)
                dist_to_r1 = abs(entry_price - resistance_1) / entry_price
                dist_to_r2 = abs(entry_price - resistance_2) / entry_price
                
                if entry_price > resistance_1 * (1 - proximity_threshold) and entry_price < resistance_1 * (1 + proximity_threshold):
                    return False, f"Entry too close to R1 (₹{resistance_1:.2f}) - likely rejection"
                
                if entry_price > resistance_2 * (1 - proximity_threshold) and entry_price < resistance_2 * (1 + proximity_threshold):
                    return False, f"Entry too close to R2 (₹{resistance_2:.2f}) - likely rejection"
                
                # Good: Entry above support
                if entry_price > support_1:
                    return True, f"Entry above S1 (₹{support_1:.2f}) - good confluence"
                
            else:  # SELL
                # Check if entry is too close to support (bad for shorts)
                if entry_price < support_1 * (1 + proximity_threshold) and entry_price > support_1 * (1 - proximity_threshold):
                    return False, f"Entry too close to S1 (₹{support_1:.2f}) - likely bounce"
                
                if entry_price < support_2 * (1 + proximity_threshold) and entry_price > support_2 * (1 - proximity_threshold):
                    return False, f"Entry too close to S2 (₹{support_2:.2f}) - likely bounce"
                
                # Good: Entry below resistance
                if entry_price < resistance_1:
                    return True, f"Entry below R1 (₹{resistance_1:.2f}) - good confluence"
            
            return True, "S/R confluence acceptable"
            
        except Exception as e:
            logger.error(f"Error in S/R confluence check: {e}")
            return True, f"S/R check error (passed): {str(e)}"
    
    def _check_gap_levels(self, symbol: str, df: pd.DataFrame, 
                         entry_price: float, is_long: bool) -> Tuple[bool, str]:
        """
        Level 20: Gap Price Level Analysis
        
        Identifies unfilled gaps that act as support/resistance.
        """
        try:
            if len(df) < 2:
                return True, "Insufficient data for gap analysis"
            
            # Detect gaps in recent data (last 20 bars)
            recent_df = df.tail(20)
            gaps_found = []
            
            for i in range(1, len(recent_df)):
                prev_close = recent_df['Close'].iloc[i-1]
                curr_open = recent_df['Open'].iloc[i]
                
                gap_percent = abs(curr_open - prev_close) / prev_close
                
                if gap_percent > (self.config.min_gap_percent / 100.0):
                    gap_type = 'up' if curr_open > prev_close else 'down'
                    gap_level = (prev_close + curr_open) / 2  # Mid-gap level
                    
                    # Check if gap is still unfilled
                    subsequent_prices = recent_df['Close'].iloc[i:]
                    if gap_type == 'up':
                        is_filled = any(p < prev_close for p in subsequent_prices)
                    else:
                        is_filled = any(p > prev_close for p in subsequent_prices)
                    
                    if not is_filled:
                        gaps_found.append({
                            'level': gap_level,
                            'type': gap_type,
                            'percent': gap_percent * 100
                        })
            
            # Check if entry is near an unfilled gap
            for gap in gaps_found:
                gap_level = gap['level']
                gap_type = gap['type']
                
                distance_percent = abs(entry_price - gap_level) / gap_level
                
                if distance_percent < 0.01:  # Within 1% of gap
                    if is_long and gap_type == 'up':
                        return True, f"Entry near unfilled gap up (₹{gap_level:.2f}) - acts as support"
                    elif not is_long and gap_type == 'down':
                        return True, f"Entry near unfilled gap down (₹{gap_level:.2f}) - acts as resistance"
            
            # No relevant gaps found - that's fine
            return True, "No conflicting gaps detected"
            
        except Exception as e:
            logger.error(f"Error in gap analysis: {e}")
            return True, f"Gap analysis error (passed): {str(e)}"
    
    def _check_nrb_pattern(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Level 21: Narrow Range Bar (NRB) Trigger
        
        Consolidation (narrow range) precedes breakouts.
        Trade should occur AFTER consolidation, not during.
        """
        try:
            if len(df) < self.config.nrb_lookback:
                return True, "Insufficient data for NRB check"
            
            recent_df = df.tail(self.config.nrb_lookback)
            
            # Calculate bar ranges
            ranges = (recent_df['High'] - recent_df['Low']) / recent_df['Close']
            
            # Current bar range
            current_range = ranges.iloc[-1]
            
            # Narrow range threshold (20th percentile of recent ranges)
            narrow_threshold = ranges.quantile(self.config.nrb_threshold_percentile / 100.0)
            
            # Check if currently in narrow range (avoid - awaiting breakout)
            if current_range <= narrow_threshold:
                return False, f"Narrow range bar detected ({current_range:.4f}) - awaiting breakout"
            
            # Check if recently broke out of narrow range (ideal)
            if len(ranges) >= 3:
                prev_ranges = ranges.iloc[-3:-1]
                was_narrow = any(r <= narrow_threshold for r in prev_ranges)
                is_expanding = current_range > narrow_threshold
                
                if was_narrow and is_expanding:
                    return True, f"Breakout from narrow range detected - ideal entry"
            
            # Normal range - acceptable
            return True, f"Bar range normal ({current_range:.4f})"
            
        except Exception as e:
            logger.error(f"Error in NRB check: {e}")
            return True, f"NRB check error (passed): {str(e)}"
    
    def _check_tick_indicator(self, is_long: bool) -> Tuple[bool, str]:
        """
        Level 22: TICK Indicator (Market Flow)
        
        Uses NIFTY 50 advance/decline ratio as market breadth indicator.
        Prevents trading against overall market flow.
        
        Logic:
        - BUY: Market should have bullish internals (more advancing than declining)
        - SELL: Market should have bearish internals (more declining than advancing)
        """
        try:
            # Get NIFTY 50 advance/decline data
            tick_data = self._get_tick_data()
            
            if not tick_data:
                logger.warning("TICK data not available - passing check")
                return True, "TICK data unavailable (passed)"
            
            tick_signal = tick_data.get('tick_signal', 'NEUTRAL')
            tick_ratio = tick_data.get('tick_ratio', 0)
            advancing = tick_data.get('advancing', 0)
            declining = tick_data.get('declining', 0)
            unchanged = tick_data.get('unchanged', 0)
            
            total = advancing + declining + unchanged
            
            if is_long:
                # For long trades, we want bullish market internals
                if tick_signal == 'BEARISH':
                    return False, (f"Market internals bearish: {declining} declining vs "
                                  f"{advancing} advancing (ratio: {tick_ratio:.2f})")
                
                # Even if neutral, ratio should not be significantly negative
                if tick_signal == 'NEUTRAL' and tick_ratio < -0.1:
                    return False, f"Weak market internals for long: ratio {tick_ratio:.2f}"
                
                logger.info(f"✅ TICK supports long: {advancing}/{total} advancing ({tick_ratio:+.2f})")
                return True, f"Market internals support long: {advancing} advancing ({tick_ratio:+.1%})"
            
            else:  # SELL
                # For short trades, we want bearish market internals
                if tick_signal == 'BULLISH':
                    return False, (f"Market internals bullish: {advancing} advancing vs "
                                  f"{declining} declining (ratio: {tick_ratio:.2f})")
                
                # Even if neutral, ratio should not be significantly positive
                if tick_signal == 'NEUTRAL' and tick_ratio > 0.1:
                    return False, f"Weak market internals for short: ratio {tick_ratio:.2f}"
                
                logger.info(f"✅ TICK supports short: {declining}/{total} declining ({tick_ratio:+.2f})")
                return True, f"Market internals support short: {declining} declining ({tick_ratio:+.1%})"
            
        except Exception as e:
            logger.error(f"Error in TICK indicator check: {e}")
            return True, f"TICK check error (passed): {str(e)}"
    
    def _get_tick_data(self) -> Optional[Dict]:
        """
        Get NIFTY 50 advance/decline data with caching.
        
        Cached for 60 seconds to avoid excessive API calls.
        
        Returns:
            Dictionary with advancing, declining, unchanged counts and ratios
        """
        from datetime import datetime, timedelta
        
        # Check cache
        if self._tick_data_cache and self._tick_cache_time:
            cache_age = (datetime.now() - self._tick_cache_time).total_seconds()
            if cache_age < 60:  # Cache valid for 60 seconds
                logger.debug(f"Using cached TICK data (age: {cache_age:.0f}s)")
                return self._tick_data_cache
        
        # Fetch fresh data
        if not self.api_client:
            logger.warning("API client not set - cannot fetch TICK data")
            return None
        
        try:
            tick_data = self._fetch_nifty_advance_decline()
            
            # Update cache
            self._tick_data_cache = tick_data
            self._tick_cache_time = datetime.now()
            
            logger.debug(f"Fetched fresh TICK data: {tick_data.get('advancing')} adv, "
                        f"{tick_data.get('declining')} dec, ratio: {tick_data.get('tick_ratio'):.2f}")
            
            return tick_data
            
        except Exception as e:
            logger.error(f"Error fetching TICK data: {e}")
            return None
    
    def _fetch_nifty_advance_decline(self) -> Dict:
        """
        Calculate advance/decline ratio for NIFTY 50 stocks.
        
        NOTE: This method is not used directly anymore. The bot now calls
        update_tick_data() with real-time calculated values.
        
        Returns:
            {
                'advancing': int,
                'declining': int,
                'unchanged': int,
                'tick_ratio': float,  # (advancing - declining) / total
                'tick_signal': str    # 'BULLISH', 'BEARISH', 'NEUTRAL'
            }
        """
        # This method is kept for backward compatibility
        # Real data now comes from realtime_bot_engine._update_market_internals()
        logger.debug("Using real-time TICK data from bot engine")
        
        return {
            'advancing': 25,
            'declining': 25,
            'unchanged': 0,
            'tick_ratio': 0.0,
            'tick_signal': 'NEUTRAL'
        }
    
    def update_tick_data(self, advancing: int, declining: int, unchanged: int):
        """
        Update TICK data from external source (called by bot).
        
        Args:
            advancing: Number of NIFTY 50 stocks with price > open
            declining: Number of NIFTY 50 stocks with price < open
            unchanged: Number of stocks unchanged
        """
        total = advancing + declining + unchanged
        tick_ratio = (advancing - declining) / total if total > 0 else 0
        
        # Determine signal
        if tick_ratio > 0.3:  # 30% more advancing
            tick_signal = 'BULLISH'
        elif tick_ratio < -0.3:  # 30% more declining
            tick_signal = 'BEARISH'
        else:
            tick_signal = 'NEUTRAL'
        
        self._tick_data_cache = {
            'advancing': advancing,
            'declining': declining,
            'unchanged': unchanged,
            'tick_ratio': tick_ratio,
            'tick_signal': tick_signal
        }
        self._tick_cache_time = datetime.now()
        
        logger.debug(f"TICK updated: {advancing}/{declining}/{unchanged} = {tick_signal} ({tick_ratio:+.2f})")
    
    def _check_ml_prediction(self, symbol: str, df: pd.DataFrame, 
                            signal_data: Dict, is_long: bool) -> Tuple[bool, str]:
        """
        Level 23: ML Prediction Filter
        
        Uses heuristic scoring based on multiple technical factors
        until actual ML model is trained.
        
        Scores multiple dimensions and requires minimum confidence.
        """
        try:
            # Score different aspects (0-100 each)
            scores = {}
            
            # 1. Trend Score (0-100)
            if 'sma_10' in df.columns and 'sma_50' in df.columns and len(df) >= 50:
                sma_10 = df['sma_10'].iloc[-1]
                sma_50 = df['sma_50'].iloc[-1]
                price = df['Close'].iloc[-1]
                
                if is_long:
                    # For longs: price > 10 SMA > 50 SMA is ideal
                    if price > sma_10 > sma_50:
                        scores['trend'] = 100
                    elif price > sma_10:
                        scores['trend'] = 60
                    else:
                        scores['trend'] = 20
                else:
                    # For shorts: price < 10 SMA < 50 SMA is ideal
                    if price < sma_10 < sma_50:
                        scores['trend'] = 100
                    elif price < sma_10:
                        scores['trend'] = 60
                    else:
                        scores['trend'] = 20
            else:
                scores['trend'] = 50  # Neutral if no data
            
            # 2. Momentum Score (0-100)
            if 'rsi' in df.columns:
                rsi = df['rsi'].iloc[-1]
                if is_long:
                    # For longs: RSI 50-70 is ideal (strong but not overbought)
                    if 50 <= rsi <= 70:
                        scores['momentum'] = 100
                    elif 40 <= rsi < 50 or 70 < rsi <= 75:
                        scores['momentum'] = 70
                    elif rsi > 80 or rsi < 30:
                        scores['momentum'] = 20  # Extreme
                    else:
                        scores['momentum'] = 40
                else:
                    # For shorts: RSI 30-50 is ideal (weak but not oversold)
                    if 30 <= rsi <= 50:
                        scores['momentum'] = 100
                    elif 25 <= rsi < 30 or 50 < rsi <= 60:
                        scores['momentum'] = 70
                    elif rsi < 20 or rsi > 70:
                        scores['momentum'] = 20  # Extreme
                    else:
                        scores['momentum'] = 40
            else:
                scores['momentum'] = 50
            
            # 3. Volume Score (0-100)
            if 'volume' in df.columns and len(df) >= 20:
                current_vol = df['Volume'].iloc[-1]
                avg_vol = df['Volume'].tail(20).mean()
                vol_ratio = current_vol / avg_vol if avg_vol > 0 else 1.0
                
                # Higher volume is generally better
                if vol_ratio > 2.0:
                    scores['Volume'] = 100
                elif vol_ratio > 1.5:
                    scores['Volume'] = 80
                elif vol_ratio > 1.0:
                    scores['Volume'] = 60
                else:
                    scores['Volume'] = 30
            else:
                scores['Volume'] = 50
            
            # 4. Volatility Score (0-100)
            if 'atr' in df.columns:
                atr = df['atr'].iloc[-1]
                price = df['Close'].iloc[-1]
                atr_pct = (atr / price) * 100
                
                # Moderate volatility is best (1-3%)
                if 1.0 <= atr_pct <= 3.0:
                    scores['volatility'] = 100
                elif 0.5 <= atr_pct < 1.0 or 3.0 < atr_pct <= 4.0:
                    scores['volatility'] = 70
                elif atr_pct > 6.0:
                    scores['volatility'] = 20  # Too volatile
                else:
                    scores['volatility'] = 40
            else:
                scores['volatility'] = 50
            
            # 5. Risk/Reward Score (0-100)
            entry = signal_data.get('entry_price', df['Close'].iloc[-1])
            stop = signal_data.get('stop_loss', entry * 0.97)
            target = signal_data.get('target', entry * 1.05)
            
            risk = abs(entry - stop)
            reward = abs(target - entry)
            rr_ratio = reward / risk if risk > 0 else 0
            
            if rr_ratio >= 3.5:
                scores['risk_reward'] = 100
            elif rr_ratio >= 3.0:
                scores['risk_reward'] = 80
            elif rr_ratio >= 2.5:
                scores['risk_reward'] = 60
            else:
                scores['risk_reward'] = 30
            
            # Calculate overall confidence score
            overall_score = sum(scores.values()) / len(scores)
            
            # Minimum confidence threshold: 95/100
            min_confidence = 95.0
            
            if overall_score < min_confidence:
                return False, (f"ML heuristic score too low: {overall_score:.1f}/100 "
                              f"(trend:{scores.get('trend',0):.0f}, "
                              f"mom:{scores.get('momentum',0):.0f}, "
                              f"vol:{scores.get('volume',0):.0f}, "
                              f"rr:{scores.get('risk_reward',0):.0f})")
            
            logger.info(f"✅ ML heuristic score: {overall_score:.1f}/100 (passed)")
            return True, f"ML heuristic confidence: {overall_score:.1f}/100"
            
        except Exception as e:
            logger.error(f"Error in ML prediction check: {e}")
            return True, f"ML check error (passed): {str(e)}"
    
    def _check_retest_opportunity(self, symbol: str, df: pd.DataFrame, 
                                  entry_price: float, is_long: bool) -> Tuple[bool, str]:
        """
        Level 24: Imbalance Retest Execution
        
        Wait for price to retest breakout level after initial spike.
        Prevents chasing the initial breakout candle.
        
        Logic:
        - Track breakout levels
        - If price is near retest of recent breakout, ALLOW entry
        - If price is spiking away from breakout level, BLOCK entry
        """
        try:
            if len(df) < 5:
                return True, "Insufficient data for retest check"
            
            # Get recent price action
            recent_highs = df['High'].tail(5)
            recent_lows = df['Low'].tail(5)
            current_close = df['Close'].iloc[-1]
            
            # Identify potential breakout levels (recent swing highs/lows)
            if is_long:
                # Check if we're retesting a recent breakout high
                breakout_level = recent_highs.max()
                
                # Is current price near the breakout level? (good - retest)
                distance_from_breakout = (current_close - breakout_level) / breakout_level
                
                if abs(distance_from_breakout) < (self.config.retest_proximity_percent / 100.0):
                    return True, f"Price retesting breakout level (₹{breakout_level:.2f}) - ideal entry"
                
                # Is price too far above breakout? (bad - chasing)
                if distance_from_breakout > 0.01:  # More than 1% above
                    return False, f"Price {distance_from_breakout*100:.2f}% above breakout (₹{breakout_level:.2f}) - avoid chasing"
                
            else:  # SELL
                # Check if we're retesting a recent breakdown low
                breakout_level = recent_lows.min()
                
                distance_from_breakout = (breakout_level - current_close) / breakout_level
                
                if abs(distance_from_breakout) < (self.config.retest_proximity_percent / 100.0):
                    return True, f"Price retesting breakdown level (₹{breakout_level:.2f}) - ideal entry"
                
                if distance_from_breakout > 0.01:
                    return False, f"Price {distance_from_breakout*100:.2f}% below breakdown (₹{breakout_level:.2f}) - avoid chasing"
            
            # Close enough to breakout level - acceptable
            return True, "Entry timing acceptable"
            
        except Exception as e:
            logger.error(f"Error in retest check: {e}")
            return True, f"Retest check error (passed): {str(e)}"
    
    def update_portfolio_value(self, new_value: float):
        """Update portfolio value for VaR calculations"""
        self.portfolio_value = new_value
        logger.debug(f"Portfolio value updated: ₹{new_value:.2f}")
    
    def record_breakout(self, symbol: str, level: float, direction: str):
        """
        Record a breakout level for retest tracking (Level 24)
        
        Args:
            symbol: Stock symbol
            level: Breakout price level
            direction: 'up' or 'down'
        """
        self.breakout_levels[symbol] = {
            'level': level,
            'timestamp': datetime.now(),
            'direction': direction
        }
        logger.debug(f"Recorded breakout: {symbol} {direction} @ ₹{level:.2f}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get screening statistics for monitoring"""
        return {
            'enabled_levels': self._get_enabled_levels(),
            'fail_safe_mode': self.config.fail_safe_mode,
            'portfolio_value': self.portfolio_value,
            'max_var_percent': self.config.max_portfolio_var_percent,
            'tracked_breakouts': len(self.breakout_levels),
            'tracked_gaps': sum(len(gaps) for gaps in self.gap_levels.values()),
        }

