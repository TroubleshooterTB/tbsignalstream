"""
Signal Quality Scoring - Phase 4
Score signals from 0-100 based on pattern quality
"""

import logging
from typing import Dict, Any, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class SignalQualityScorer:
    """
    Score signal quality from 0-100 based on multiple factors
    
    Scoring breakdown:
    - Pattern Strength: 25 points
    - Market Conditions: 20 points
    - Technical Confluence: 20 points
    - Risk/Reward: 15 points
    - Volume: 10 points
    - Trend Alignment: 10 points
    """
    
    def __init__(self):
        self.min_acceptable_score = 60  # Signals below 60 are flagged
        
    def score_signal(self, signal_data: Dict[str, Any], df: pd.DataFrame, 
                    market_data: Dict[str, Any] = None) -> Tuple[float, Dict[str, float], str]:
        """
        Score a trading signal
        
        Returns:
            - Total score (0-100)
            - Breakdown dict
            - Quality grade (A+, A, B, C, D, F)
        """
        try:
            breakdown = {}
            
            # 1. Pattern Strength (25 points)
            pattern_score = self._score_pattern_strength(signal_data, df)
            breakdown['pattern_strength'] = pattern_score
            
            # 2. Market Conditions (20 points)
            market_score = self._score_market_conditions(df, market_data)
            breakdown['market_conditions'] = market_score
            
            # 3. Technical Confluence (20 points)
            confluence_score = self._score_technical_confluence(df)
            breakdown['technical_confluence'] = confluence_score
            
            # 4. Risk/Reward (15 points)
            rr_score = self._score_risk_reward(signal_data)
            breakdown['risk_reward'] = rr_score
            
            # 5. Volume (10 points)
            volume_score = self._score_volume(df)
            breakdown['volume'] = volume_score
            
            # 6. Trend Alignment (10 points)
            trend_score = self._score_trend_alignment(signal_data, df)
            breakdown['trend_alignment'] = trend_score
            
            # Total score
            total_score = sum(breakdown.values())
            
            # Grade
            grade = self._get_grade(total_score)
            
            logger.debug(f"Signal Quality: {total_score:.1f} ({grade}) - {signal_data.get('symbol', 'UNKNOWN')}")
            
            return total_score, breakdown, grade
            
        except Exception as e:
            logger.error(f"Error scoring signal: {e}", exc_info=True)
            return 50.0, {}, 'C'  # Default to average
    
    def _score_pattern_strength(self, signal_data: Dict[str, Any], df: pd.DataFrame) -> float:
        """Score pattern quality (0-25 points)"""
        score = 0.0
        
        try:
            # Get pattern confidence if available
            confidence = signal_data.get('confidence', 0.5)
            score += confidence * 15  # Up to 15 points from confidence
            
            # Check if near support/resistance
            if 'support' in signal_data or 'resistance' in signal_data:
                score += 5
            
            # Check if breakout confirmed
            if signal_data.get('breakout_confirmed', False):
                score += 5
            
        except Exception as e:
            logger.debug(f"Pattern scoring error: {e}")
        
        return min(score, 25.0)
    
    def _score_market_conditions(self, df: pd.DataFrame, market_data: Dict[str, Any] = None) -> float:
        """Score market conditions (0-20 points)"""
        score = 0.0
        
        try:
            # VIX check (if available)
            if market_data and 'vix' in market_data:
                vix = market_data['vix']
                if vix < 15:
                    score += 10  # Low volatility = good
                elif vix < 25:
                    score += 5   # Medium volatility = okay
                # High VIX = no points
            else:
                score += 5  # Default if no VIX data
            
            # Nifty alignment (if available)
            if market_data and 'nifty_trend' in market_data:
                nifty_trend = market_data['nifty_trend']
                signal_direction = df['close'].iloc[-1] > df['close'].iloc[-5]
                
                # Aligned with market = good
                if (nifty_trend == 'up' and signal_direction) or \
                   (nifty_trend == 'down' and not signal_direction):
                    score += 10
                else:
                    score += 3  # Against market = risky
            else:
                score += 5  # Default
                
        except Exception as e:
            logger.debug(f"Market conditions scoring error: {e}")
            score = 10  # Default to middle
        
        return min(score, 20.0)
    
    def _score_technical_confluence(self, df: pd.DataFrame) -> float:
        """Score technical indicator confluence (0-20 points)"""
        score = 0.0
        
        try:
            # Check how many indicators agree
            last_close = df['close'].iloc[-1]
            
            # EMA alignment
            if 'ema_50' in df.columns:
                ema_50 = df['ema_50'].iloc[-1]
                if abs(last_close - ema_50) / ema_50 < 0.02:  # Within 2%
                    score += 5
            
            # RSI in good range
            if 'rsi' in df.columns:
                rsi = df['rsi'].iloc[-1]
                if 40 < rsi < 60:
                    score += 5
                elif 30 < rsi < 70:
                    score += 3
            
            # MACD alignment
            if 'macd' in df.columns and 'macd_signal' in df.columns:
                macd = df['macd'].iloc[-1]
                macd_signal = df['macd_signal'].iloc[-1]
                
                # Bullish crossover or bearish crossover
                if abs(macd - macd_signal) < abs(df['macd'].iloc[-2] - df['macd_signal'].iloc[-2]):
                    score += 5
            
            # Bollinger Bands
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
                bb_position = (last_close - df['bb_lower'].iloc[-1]) / (df['bb_upper'].iloc[-1] - df['bb_lower'].iloc[-1])
                
                # Not at extremes = good
                if 0.3 < bb_position < 0.7:
                    score += 5
                    
        except Exception as e:
            logger.debug(f"Confluence scoring error: {e}")
            score = 10  # Default
        
        return min(score, 20.0)
    
    def _score_risk_reward(self, signal_data: Dict[str, Any]) -> float:
        """Score risk/reward ratio (0-15 points)"""
        score = 0.0
        
        try:
            entry = signal_data.get('entry_price', 0)
            stop_loss = signal_data.get('stop_loss', 0)
            target = signal_data.get('target', 0)
            
            if entry and stop_loss and target:
                risk = abs(entry - stop_loss)
                reward = abs(target - entry)
                
                if risk > 0:
                    rr_ratio = reward / risk
                    
                    if rr_ratio >= 3.0:
                        score = 15  # 3:1 or better = excellent
                    elif rr_ratio >= 2.5:
                        score = 12  # 2.5:1 = great
                    elif rr_ratio >= 2.0:
                        score = 10  # 2:1 = good
                    elif rr_ratio >= 1.5:
                        score = 7   # 1.5:1 = acceptable
                    else:
                        score = 3   # Below 1.5:1 = poor
            else:
                score = 7  # Default if data missing
                
        except Exception as e:
            logger.debug(f"R:R scoring error: {e}")
            score = 7  # Default
        
        return min(score, 15.0)
    
    def _score_volume(self, df: pd.DataFrame) -> float:
        """Score volume confirmation (0-10 points)"""
        score = 0.0
        
        try:
            if 'volume' in df.columns and len(df) >= 20:
                current_volume = df['volume'].iloc[-1]
                avg_volume_20 = df['volume'].iloc[-20:].mean()
                
                if avg_volume_20 > 0:
                    volume_ratio = current_volume / avg_volume_20
                    
                    if volume_ratio >= 2.5:
                        score = 10  # Very high volume = excellent
                    elif volume_ratio >= 2.0:
                        score = 8   # High volume = great
                    elif volume_ratio >= 1.5:
                        score = 6   # Above average = good
                    elif volume_ratio >= 1.0:
                        score = 4   # Normal = acceptable
                    else:
                        score = 2   # Low volume = concerning
            else:
                score = 5  # Default if no volume data
                
        except Exception as e:
            logger.debug(f"Volume scoring error: {e}")
            score = 5  # Default
        
        return min(score, 10.0)
    
    def _score_trend_alignment(self, signal_data: Dict[str, Any], df: pd.DataFrame) -> float:
        """Score trend alignment (0-10 points)"""
        score = 0.0
        
        try:
            direction = signal_data.get('direction', 'up')
            
            # Check EMA trend
            if 'ema_50' in df.columns and len(df) >= 10:
                ema_current = df['ema_50'].iloc[-1]
                ema_past = df['ema_50'].iloc[-10]
                ema_trending_up = ema_current > ema_past
                
                # Aligned with EMA trend
                if (direction == 'up' and ema_trending_up) or (direction == 'down' and not ema_trending_up):
                    score += 5
                else:
                    score += 2  # Counter-trend = risky
            
            # Check ADX (trend strength)
            if 'adx' in df.columns:
                adx = df['adx'].iloc[-1]
                
                if adx >= 25:
                    score += 5  # Strong trend
                elif adx >= 20:
                    score += 3  # Moderate trend
                else:
                    score += 1  # Weak trend
            else:
                score += 3  # Default
                
        except Exception as e:
            logger.debug(f"Trend scoring error: {e}")
            score = 5  # Default
        
        return min(score, 10.0)
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return 'A+'
        elif score >= 85:
            return 'A'
        elif score >= 80:
            return 'A-'
        elif score >= 75:
            return 'B+'
        elif score >= 70:
            return 'B'
        elif score >= 65:
            return 'B-'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        elif score >= 50:
            return 'C-'
        elif score >= 40:
            return 'D'
        else:
            return 'F'
    
    def is_acceptable(self, score: float) -> bool:
        """Check if score meets minimum threshold"""
        return score >= self.min_acceptable_score
