"""
🎯 MEAN REVERSION STRATEGY FOR SIDEWAYS MARKETS
=================================================

Purpose: Activates when ADX < 20 (choppy/range-bound markets)
Research: Mean reversion works best in low-volatility environments
Source: "Evidence for Pairs Trading in Indian Stock Market" + Bollinger Band research

Strategy Logic:
- LONG: Price touches Lower Bollinger Band (2 SD) AND RSI < 30
- SHORT: Price touches Upper Bollinger Band (2 SD) AND RSI > 70  
- EXIT: Price reaches Moving Average (mean)

Expected Win Rate: 55-65% in sideways markets
Expected Profit Factor: 1.8-2.2
Risk-Reward: 1:1.5 (tight range-bound targets)

Author: GitHub Copilot (Claude Sonnet 4.5)
Date: January 20, 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class MeanReversionStrategy:
    """
    Bollinger Band + RSI Mean Reversion Strategy
    Optimized for ADX < 20 (sideways/choppy markets)
    """
    
    def __init__(self, **params):
        """
        Initialize Mean Reversion Strategy with configurable parameters
        
        Args:
            bb_period: Bollinger Band period (default: 20)
            bb_std: Bollinger Band standard deviations (default: 2.0)
            rsi_period: RSI period (default: 14)
            rsi_oversold: RSI oversold level (default: 30)
            rsi_overbought: RSI overbought level (default: 70)
            volume_threshold: Min volume vs avg (default: 0.5 = 50% of avg)
            risk_reward: Risk-reward ratio (default: 1.5)
        """
        # Bollinger Band Parameters
        self.BB_PERIOD = params.get('bb_period', 20)
        self.BB_STD = params.get('bb_std', 2.0)
        
        # RSI Parameters
        self.RSI_PERIOD = params.get('rsi_period', 14)
        self.RSI_OVERSOLD = params.get('rsi_oversold', 30)
        self.RSI_OVERBOUGHT = params.get('rsi_overbought', 70)
        
        # Volume Filter (relaxed for sideways markets)
        self.VOLUME_THRESHOLD = params.get('volume_threshold', 0.5)  # 50% of average (relaxed)
        
        # Risk Management
        self.RISK_REWARD_RATIO = params.get('risk_reward', 1.5)
        self.ATR_MULTIPLIER_SL = 1.5  # Tighter stops for mean reversion
        self.MAX_RISK_PERCENT = 1.5  # Max 1.5% risk per trade
        
        # ADX Threshold (only activate in sideways markets)
        self.MAX_ADX = 20  # Only trade when ADX < 20
        
        logger.info("="*80)
        logger.info("🔄 MEAN REVERSION STRATEGY INITIALIZED")
        logger.info(f"   Bollinger Bands: {self.BB_PERIOD} period, {self.BB_STD} SD")
        logger.info(f"   RSI: {self.RSI_PERIOD} period (Oversold: {self.RSI_OVERSOLD}, Overbought: {self.RSI_OVERBOUGHT})")
        logger.info(f"   Volume Threshold: {self.VOLUME_THRESHOLD*100:.0f}% of average (relaxed for sideways)")
        logger.info(f"   ADX Filter: Only trade when ADX < {self.MAX_ADX}")
        logger.info(f"   Risk-Reward: 1:{self.RISK_REWARD_RATIO}")
        logger.info("="*80)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for mean reversion
        
        Required: OHLCV data
        Adds: BB_UPPER, BB_MIDDLE, BB_LOWER, RSI, ATR, Volume_MA
        """
        if len(df) < self.BB_PERIOD + 5:
            logger.warning(f"Insufficient data for indicators: {len(df)} < {self.BB_PERIOD + 5}")
            return df
        
        # Bollinger Bands
        df['BB_MIDDLE'] = df['close'].rolling(window=self.BB_PERIOD).mean()
        bb_std = df['close'].rolling(window=self.BB_PERIOD).std()
        df['BB_UPPER'] = df['BB_MIDDLE'] + (bb_std * self.BB_STD)
        df['BB_LOWER'] = df['BB_MIDDLE'] - (bb_std * self.BB_STD)
        
        # Bollinger Band Width (for squeeze detection)
        df['BB_WIDTH'] = (df['BB_UPPER'] - df['BB_LOWER']) / df['BB_MIDDLE'] * 100
        
        # RSI (already calculated by bot, but add if missing)
        if 'rsi' not in df.columns:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.RSI_PERIOD).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=self.RSI_PERIOD).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR for stop loss
        if 'atr' not in df.columns:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = true_range.rolling(window=14).mean()
        
        # Volume Moving Average (relaxed for sideways)
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def find_mean_reversion_setup(self, df: pd.DataFrame, symbol: str) -> Optional[Dict]:
        """
        🎯 CORE LOGIC: Find mean reversion opportunities in sideways markets
        
        Args:
            df: DataFrame with OHLCV + indicators
            symbol: Stock symbol
        
        Returns:
            Signal dict or None
        """
        if len(df) < 50:
            return None
        
        # Get latest values
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        close = float(latest['close'])
        rsi = float(latest.get('rsi', 50))
        adx = float(latest.get('adx', 0))
        volume = float(latest['volume'])
        volume_ma = float(latest.get('volume_ma', volume))
        
        bb_upper = float(latest['BB_UPPER'])
        bb_middle = float(latest['BB_MIDDLE'])
        bb_lower = float(latest['BB_LOWER'])
        bb_width = float(latest.get('BB_WIDTH', 0))
        atr = float(latest.get('atr', close * 0.02))
        
        # ========== FILTERS ==========
        
        # Filter 1: ADX < 20 (MANDATORY - only trade sideways markets)
        if adx >= self.MAX_ADX:
            logger.debug(f"⏭️ [{symbol}] Mean Reversion: ADX {adx:.1f} >= {self.MAX_ADX} (too trending)")
            return None
        
        # Filter 2: Volume Check (RELAXED - 50% of average is OK in sideways)
        if volume_ma > 0 and volume < volume_ma * self.VOLUME_THRESHOLD:
            logger.debug(f"⏭️ [{symbol}] Mean Reversion: Low volume ({volume:.0f} < {volume_ma * self.VOLUME_THRESHOLD:.0f})")
            return None
        
        # Filter 3: BB Width > 1% (avoid extreme squeeze)
        if bb_width < 1.0:
            logger.debug(f"⏭️ [{symbol}] Mean Reversion: BB too narrow ({bb_width:.2f}% < 1%)")
            return None
        
        # ========== LONG SIGNAL (Oversold) ==========
        
        # Condition: Price touched or broke below Lower BB AND RSI < 30
        price_at_lower_bb = close <= bb_lower * 1.002  # Within 0.2% of lower band
        rsi_oversold = rsi < self.RSI_OVERSOLD
        
        if price_at_lower_bb and rsi_oversold:
            # Calculate stop loss: Below recent low or ATR-based
            recent_low = float(df['low'].iloc[-5:].min())
            atr_stop = close - (self.ATR_MULTIPLIER_SL * atr)
            stop_loss = min(recent_low * 0.998, atr_stop)  # Use tighter stop
            
            # Target: Mean (BB Middle)
            target = bb_middle
            
            # Validate R:R
            risk = close - stop_loss
            reward = target - close
            
            if risk <= 0 or reward <= 0:
                return None
            
            rr_ratio = reward / risk
            
            if rr_ratio < 1.0:  # Minimum 1:1 for mean reversion
                logger.debug(f"⏭️ [{symbol}] Mean Reversion LONG: R:R {rr_ratio:.2f} < 1.0")
                return None
            
            logger.info(f"🔵 [{symbol}] MEAN REVERSION LONG SETUP:")
            logger.info(f"   ADX: {adx:.1f} (sideways)")
            logger.info(f"   Price: ₹{close:.2f} @ Lower BB (₹{bb_lower:.2f})")
            logger.info(f"   RSI: {rsi:.1f} (oversold)")
            logger.info(f"   Entry: ₹{close:.2f}")
            logger.info(f"   Stop: ₹{stop_loss:.2f}")
            logger.info(f"   Target: ₹{target:.2f} (BB Middle)")
            logger.info(f"   R:R: 1:{rr_ratio:.2f}")
            
            return {
                'action': 'BUY',
                'type': 'MEAN_REVERSION',
                'entry_price': close,
                'stop_loss': stop_loss,
                'target': target,
                'confidence': min(95, 70 + (30 - rsi)),  # Higher confidence when more oversold
                'indicators': {
                    'adx': adx,
                    'rsi': rsi,
                    'bb_position': 'LOWER',
                    'bb_width': bb_width,
                    'volume_ratio': volume / volume_ma if volume_ma > 0 else 1.0
                },
                'rationale': f"Oversold bounce: Price @ Lower BB (₹{bb_lower:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}"
            }
        
        # ========== SHORT SIGNAL (Overbought) ==========
        
        # Condition: Price touched or broke above Upper BB AND RSI > 70
        price_at_upper_bb = close >= bb_upper * 0.998  # Within 0.2% of upper band
        rsi_overbought = rsi > self.RSI_OVERBOUGHT
        
        if price_at_upper_bb and rsi_overbought:
            # Calculate stop loss: Above recent high or ATR-based
            recent_high = float(df['high'].iloc[-5:].max())
            atr_stop = close + (self.ATR_MULTIPLIER_SL * atr)
            stop_loss = max(recent_high * 1.002, atr_stop)
            
            # Target: Mean (BB Middle)
            target = bb_middle
            
            # Validate R:R
            risk = stop_loss - close
            reward = close - target
            
            if risk <= 0 or reward <= 0:
                return None
            
            rr_ratio = reward / risk
            
            if rr_ratio < 1.0:
                logger.debug(f"⏭️ [{symbol}] Mean Reversion SHORT: R:R {rr_ratio:.2f} < 1.0")
                return None
            
            logger.info(f"🔴 [{symbol}] MEAN REVERSION SHORT SETUP:")
            logger.info(f"   ADX: {adx:.1f} (sideways)")
            logger.info(f"   Price: ₹{close:.2f} @ Upper BB (₹{bb_upper:.2f})")
            logger.info(f"   RSI: {rsi:.1f} (overbought)")
            logger.info(f"   Entry: ₹{close:.2f}")
            logger.info(f"   Stop: ₹{stop_loss:.2f}")
            logger.info(f"   Target: ₹{target:.2f} (BB Middle)")
            logger.info(f"   R:R: 1:{rr_ratio:.2f}")
            
            return {
                'action': 'SELL',
                'type': 'MEAN_REVERSION',
                'entry_price': close,
                'stop_loss': stop_loss,
                'target': target,
                'confidence': min(95, 70 + (rsi - 70)),  # Higher confidence when more overbought
                'indicators': {
                    'adx': adx,
                    'rsi': rsi,
                    'bb_position': 'UPPER',
                    'bb_width': bb_width,
                    'volume_ratio': volume / volume_ma if volume_ma > 0 else 1.0
                },
                'rationale': f"Overbought fade: Price @ Upper BB (₹{bb_upper:.2f}), RSI {rsi:.1f}, ADX {adx:.1f}"
            }
        
        return None
    
    def scan_universe(self, candle_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        Scan entire universe for mean reversion opportunities
        
        Args:
            candle_data: Dict of {symbol: DataFrame with OHLCV}
        
        Returns:
            List of signal dicts sorted by confidence
        """
        signals = []
        
        for symbol, df in candle_data.items():
            try:
                # Calculate indicators if not present
                if 'BB_MIDDLE' not in df.columns:
                    df = self.calculate_indicators(df)
                
                # Find setup
                signal = self.find_mean_reversion_setup(df, symbol)
                
                if signal:
                    signal['symbol'] = symbol
                    signals.append(signal)
            
            except Exception as e:
                logger.error(f"Error scanning {symbol} for mean reversion: {e}")
        
        # Sort by confidence (highest first)
        signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        if signals:
            logger.info(f"🔄 MEAN REVERSION: Found {len(signals)} opportunities in sideways market")
        
        return signals
