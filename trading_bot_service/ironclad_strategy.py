# ==============================================================================
# Ironclad Trading Strategy - Sidecar Module
# A stateless, production-grade trading logic implementation
# ==============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import pytz
import logging
from typing import Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IroncladStrategy:
    """
    Ironclad Trading Strategy - Defining Range Breakout with Multi-Timeframe Confirmation
    
    Strategy Logic:
    1. Define Range (DR): 09:15-10:15 IST - Capture high/low
    2. Regime Filter: NIFTY trend + ADX strength
    3. Entry: Breakout of DR with confirmations
    4. Risk: ATR-based stops with 1.5:1 risk-reward
    
    Stateless Design: All state persisted to Firestore
    """
    
    def __init__(self, db_client, dr_window_minutes: int = 60):
        """
        Initialize strategy with Firestore client.
        
        Args:
            db_client: Firebase Firestore client instance
            dr_window_minutes: Defining Range window in minutes (default 60)
        """
        self.db = db_client
        self.ist_tz = pytz.timezone('Asia/Kolkata')
        
        # Strategy parameters (immutable)
        self.DR_WINDOW_MINUTES = dr_window_minutes  # Dynamic DR window
        self.ADX_THRESHOLD = 20        # Minimum ADX for trend
        self.ATR_STOP_MULTIPLIER = 3.0 # Stop loss distance
        self.RISK_REWARD_RATIO = 1.5   # Target distance multiplier
        
        logger.info(f"[IroncladStrategy] Initialized with {dr_window_minutes}-min DR window")
    
    def get_bot_state(self, symbol: str) -> Dict:
        """
        Retrieve bot state from Firestore for given symbol.
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            
        Returns:
            Dictionary with 'dr_high', 'dr_low', 'regime', 'last_updated'
        """
        try:
            doc_ref = self.db.collection('bot_state').document(symbol)
            doc = doc_ref.get()
            
            if doc.exists:
                state = doc.to_dict()
                logger.info(f"[{symbol}] Loaded state: DR High={state.get('dr_high')}, "
                           f"DR Low={state.get('dr_low')}, Regime={state.get('regime')}")
                return state
            else:
                logger.info(f"[{symbol}] No existing state found")
                return {}
        except Exception as e:
            logger.error(f"[{symbol}] Error loading state: {e}")
            return {}
    
    def save_bot_state(self, symbol: str, data_dict: Dict) -> bool:
        """
        Save bot state to Firestore.
        
        Args:
            symbol: Stock symbol
            data_dict: Dictionary with 'dr_high', 'dr_low', 'regime', etc.
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.db.collection('bot_state').document(symbol)
            data_dict['last_updated'] = datetime.now(self.ist_tz)
            doc_ref.set(data_dict, merge=True)
            
            logger.info(f"[{symbol}] Saved state: {data_dict}")
            return True
        except Exception as e:
            logger.error(f"[{symbol}] Error saving state: {e}")
            return False
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all required technical indicators using pandas_ta.
        
        Args:
            df: DataFrame with OHLCV columns
            
        Returns:
            DataFrame with added indicator columns
        """
        if df.empty or len(df) < 200:
            logger.warning(f"Insufficient data: {len(df)} candles (need 200+)")
            return df
        
        # Ensure index is DatetimeIndex for VWAP
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df.index = pd.to_datetime(df['timestamp'])
            elif 'date' in df.columns:
                df.index = pd.to_datetime(df['date'])
        
        # Make column names lowercase for pandas_ta compatibility
        df.columns = df.columns.str.lower()
        
        try:
            # ADX (14) - Manual calculation
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            
            df['high_diff'] = df['high'] - df['high'].shift(1)
            df['low_diff'] = df['low'].shift(1) - df['low']
            
            df['plus_dm'] = np.where((df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0), df['high_diff'], 0)
            df['minus_dm'] = np.where((df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0), df['low_diff'], 0)
            
            atr_14 = df['tr'].rolling(window=14).mean()
            # Prevent division by zero in DI calculations
            plus_di = 100 * (df['plus_dm'].rolling(window=14).mean() / atr_14.replace(0, 1e-10))
            minus_di = 100 * (df['minus_dm'].rolling(window=14).mean() / atr_14.replace(0, 1e-10))
            
            # Prevent division by zero in DX calculation
            di_sum = plus_di + minus_di
            dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, 1e-10)
            df['adx'] = dx.rolling(window=14).mean()
            df['dmi_plus'] = plus_di
            df['dmi_minus'] = minus_di
            
            # Simple Moving Averages
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_100'] = df['close'].rolling(window=100).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            # VWAP (requires intraday data with DatetimeIndex)
            if isinstance(df.index, pd.DatetimeIndex):
                df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
            else:
                df['vwap'] = (df['high'] + df['low'] + df['close']) / 3  # Fallback to typical price
            
            # MACD (12, 26, 9)
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # RSI (14)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            # Prevent division by zero
            rs = gain / loss.replace(0, 1e-10)
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # ATR (14)
            df['atr'] = atr_14
            
            # Volume SMA (10)
            df['volume_sma'] = df['volume'].rolling(window=10).mean()
            
            # Bollinger Bands (20, 2)
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
            df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
            # Prevent division by zero in BB calculations
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle'].replace(0, 1e-10)
            bb_range = (df['bb_upper'] - df['bb_lower']).replace(0, 1e-10)
            df['bb_position'] = (df['close'] - df['bb_lower']) / bb_range
            
            # Stochastic Oscillator (14, 3, 3)
            lowest_low = df['low'].rolling(window=14).min()
            highest_high = df['high'].rolling(window=14).max()
            # Prevent division by zero in Stochastic
            stoch_range = (highest_high - lowest_low).replace(0, 1e-10)
            df['stoch_k'] = 100 * (df['close'] - lowest_low) / stoch_range
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # Exponential Moving Averages
            df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
            df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
            
            # On-Balance Volume (OBV)
            df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
            df['obv_sma'] = df['obv'].rolling(window=20).mean()
            
            # Williams %R (14) - prevent division by zero
            wr_range = (highest_high - lowest_low).replace(0, 1e-10)
            df['williams_r'] = -100 * (highest_high - df['close']) / wr_range
            
            # Average Directional Movement Index (ADX already calculated above)
            # Price Rate of Change (ROC) - 12 period - prevent division by zero
            df['roc'] = ((df['close'] - df['close'].shift(12)) / df['close'].shift(12).replace(0, 1e-10)) * 100
            
            # Commodity Channel Index (CCI) - 20 period - prevent division by zero
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = typical_price.rolling(window=20).mean()
            mean_deviation = typical_price.rolling(window=20).apply(lambda x: np.abs(x - x.mean()).mean())
            df['cci'] = (typical_price - sma_tp) / (0.015 * mean_deviation.replace(0, 1e-10))
            
            # Money Flow Index (MFI) - 14 period - prevent division by zero
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            money_flow = typical_price * df['volume']
            positive_flow = money_flow.where(df['close'] > df['close'].shift(1), 0).rolling(window=14).sum()
            negative_flow = money_flow.where(df['close'] < df['close'].shift(1), 0).rolling(window=14).sum()
            money_ratio = positive_flow / negative_flow.replace(0, 1e-10)
            df['mfi'] = 100 - (100 / (1 + money_ratio))
            
            # Parabolic SAR (simplified version)
            df['psar'] = df['close'].rolling(window=2).mean()  # Simplified - full implementation is complex
            
            # Support and Resistance levels (using pivot points)
            df['pivot'] = (df['high'] + df['low'] + df['close']) / 3
            df['resistance_1'] = 2 * df['pivot'] - df['low']
            df['support_1'] = 2 * df['pivot'] - df['high']
            df['resistance_2'] = df['pivot'] + (df['high'] - df['low'])
            df['support_2'] = df['pivot'] - (df['high'] - df['low'])
            
            # Trend strength indicator
            df['trend_strength'] = abs(df['close'] - df['sma_50']) / df['sma_50'] * 100
            
            # Volume trend
            df['volume_trend'] = df['volume'] / df['volume_sma']
            
            logger.info(f"Calculated {len([col for col in df.columns if col not in ['open', 'high', 'low', 'close', 'volume']])} technical indicators for {len(df)} candles")
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
        
        return df
    
    def check_regime(self, nifty_df: pd.DataFrame, stock_df: pd.DataFrame) -> str:
        """
        Determine market regime using NIFTY trend strength and stock confirmation.
        
        Logic:
        1. NIFTY ADX > 20 (trending market)
        2. NIFTY SMA alignment: 10>20>50>100>200 (Bullish) or inverse (Bearish)
        3. Stock price vs VWAP confirmation
        
        Args:
            nifty_df: NIFTY 50 DataFrame with indicators
            stock_df: Stock DataFrame with indicators
            
        Returns:
            "BULLISH", "BEARISH", or "NEUTRAL"
        """
        if nifty_df.empty or stock_df.empty:
            logger.warning("Empty dataframes for regime check")
            return "NEUTRAL"
        
        try:
            # Get latest values
            nifty_latest = nifty_df.iloc[-1]
            stock_latest = stock_df.iloc[-1]
            
            # Check 1: NIFTY ADX strength
            nifty_adx = nifty_latest.get('adx', 0)
            if nifty_adx < self.ADX_THRESHOLD:
                logger.info(f"NIFTY ADX={nifty_adx:.2f} below threshold {self.ADX_THRESHOLD}")
                return "NEUTRAL"
            
            # Check 2: NIFTY SMA alignment
            sma_10 = nifty_latest.get('sma_10', 0)
            sma_20 = nifty_latest.get('sma_20', 0)
            sma_50 = nifty_latest.get('sma_50', 0)
            sma_100 = nifty_latest.get('sma_100', 0)
            sma_200 = nifty_latest.get('sma_200', 0)
            
            # Bullish: 10 > 20 > 50 > 100 > 200
            is_bullish_alignment = (sma_10 > sma_20 > sma_50 > sma_100 > sma_200)
            
            # Bearish: 10 < 20 < 50 < 100 < 200
            is_bearish_alignment = (sma_10 < sma_20 < sma_50 < sma_100 < sma_200)
            
            # Check 3: Stock price vs VWAP confirmation
            stock_price = stock_latest.get('close', 0)
            stock_vwap = stock_latest.get('vwap', stock_price)
            
            if is_bullish_alignment:
                if stock_price > stock_vwap:
                    logger.info(f"Regime: BULLISH (NIFTY ADX={nifty_adx:.2f}, Price > VWAP)")
                    return "BULLISH"
                else:
                    logger.info(f"Regime: NEUTRAL (Bullish NIFTY but Stock below VWAP)")
                    return "NEUTRAL"
            
            elif is_bearish_alignment:
                if stock_price < stock_vwap:
                    logger.info(f"Regime: BEARISH (NIFTY ADX={nifty_adx:.2f}, Price < VWAP)")
                    return "BEARISH"
                else:
                    logger.info(f"Regime: NEUTRAL (Bearish NIFTY but Stock above VWAP)")
                    return "NEUTRAL"
            
            else:
                logger.info(f"Regime: NEUTRAL (No clear SMA alignment)")
                return "NEUTRAL"
                
        except Exception as e:
            logger.error(f"Error in regime check: {e}")
            return "NEUTRAL"
    
    def get_defining_range(self, stock_df: pd.DataFrame, bot_start_time: Optional[datetime] = None) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate Defining Range (DR) from first N minutes of data.
        
        If bot_start_time provided, uses first DR_WINDOW_MINUTES after that.
        Otherwise, uses first DR_WINDOW_MINUTES of available data.
        
        Args:
            stock_df: Stock DataFrame with DatetimeIndex
            bot_start_time: Optional bot start timestamp (IST)
            
        Returns:
            Tuple of (dr_high, dr_low) or (None, None) if insufficient data
        """
        if stock_df.empty:
            return None, None
        
        try:
            # Ensure index is timezone-aware IST
            if stock_df.index.tz is None:
                stock_df.index = stock_df.index.tz_localize('UTC').tz_convert(self.ist_tz)
            elif stock_df.index.tz != self.ist_tz:
                stock_df.index = stock_df.index.tz_convert(self.ist_tz)
            
            # Determine DR start time
            if bot_start_time:
                # Use bot start time as DR start
                dr_start = bot_start_time if bot_start_time.tzinfo else bot_start_time.replace(tzinfo=self.ist_tz)
            else:
                # Use first available data point
                dr_start = stock_df.index[0]
            
            # Calculate DR end time
            dr_end = dr_start + timedelta(minutes=self.DR_WINDOW_MINUTES)
            
            # Get candles within DR period
            dr_candles = stock_df[(stock_df.index >= dr_start) & (stock_df.index <= dr_end)]
            
            if dr_candles.empty:
                logger.warning(f"No candles found in DR period {dr_start} to {dr_end}")
                return None, None
            
            dr_high = dr_candles['high'].max()
            dr_low = dr_candles['low'].min()
            
            logger.info(f"Defining Range: High={dr_high:.2f}, Low={dr_low:.2f} "
                       f"(from {len(dr_candles)} candles)")
            
            return dr_high, dr_low
            
        except Exception as e:
            logger.error(f"Error calculating defining range: {e}")
            return None, None
    
    def check_trigger(self, stock_df: pd.DataFrame, regime: str, 
                     dr_high: float, dr_low: float) -> str:
        """
        Check for entry trigger based on DR breakout and confirmations.
        
        BUY Logic:
        - Price > DR High (breakout)
        - Regime == BULLISH
        - MACD Line > Signal Line
        - RSI >= 40 (not oversold)
        - Volume > Volume SMA (strong breakout)
        
        SELL Logic:
        - Price < DR Low (breakdown)
        - Regime == BEARISH
        - MACD Line < Signal Line
        - RSI <= 60 (not overbought)
        - Volume > Volume SMA (strong breakdown)
        
        Args:
            stock_df: Stock DataFrame with indicators
            regime: Current market regime ("BULLISH", "BEARISH", "NEUTRAL")
            dr_high: Defining Range high
            dr_low: Defining Range low
            
        Returns:
            "BUY", "SELL", or "NONE"
        """
        if stock_df.empty or regime == "NEUTRAL":
            return "NONE"
        
        try:
            latest = stock_df.iloc[-1]
            
            price = latest.get('close', 0)
            macd = latest.get('macd', 0)
            macd_signal = latest.get('macd_signal', 0)
            rsi = latest.get('rsi', 50)
            volume = latest.get('volume', 0)
            volume_sma = latest.get('volume_sma', volume)
            
            # BUY Signal
            if regime == "BULLISH":
                if (price > dr_high and
                    macd > macd_signal and
                    rsi >= 40 and
                    volume > volume_sma):
                    
                    logger.info(f"BUY TRIGGER: Price={price:.2f} > DR_High={dr_high:.2f}, "
                               f"MACD={macd:.2f} > Signal={macd_signal:.2f}, "
                               f"RSI={rsi:.2f}, Vol={volume} > SMA={volume_sma}")
                    return "BUY"
            
            # SELL Signal
            elif regime == "BEARISH":
                if (price < dr_low and
                    macd < macd_signal and
                    rsi <= 60 and
                    volume > volume_sma):
                    
                    logger.info(f"SELL TRIGGER: Price={price:.2f} < DR_Low={dr_low:.2f}, "
                               f"MACD={macd:.2f} < Signal={macd_signal:.2f}, "
                               f"RSI={rsi:.2f}, Vol={volume} > SMA={volume_sma}")
                    return "SELL"
            
            return "NONE"
            
        except Exception as e:
            logger.error(f"Error checking trigger: {e}")
            return "NONE"
    
    def calculate_risk(self, entry_price: float, direction: str, 
                      stock_df: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate stop-loss and target based on ATR.
        
        Logic:
        - Stop Loss = Entry +/- (3.0 * ATR)
        - Distance to Stop = abs(Entry - Stop)
        - Target = Entry +/- (1.5 * Distance to Stop)
        
        Args:
            entry_price: Entry price for the trade
            direction: "BUY" or "SELL"
            stock_df: Stock DataFrame with ATR indicator
            
        Returns:
            Tuple of (stop_loss, target_price)
        """
        if stock_df.empty:
            logger.warning("Empty DataFrame for risk calculation")
            # Fallback: 2% stop, 3% target
            if direction == "BUY":
                return entry_price * 0.98, entry_price * 1.03
            else:
                return entry_price * 1.02, entry_price * 0.97
        
        try:
            latest = stock_df.iloc[-1]
            atr = latest.get('atr', entry_price * 0.02)  # Default to 2% if ATR missing
            
            if direction == "BUY":
                stop_loss = entry_price - (self.ATR_STOP_MULTIPLIER * atr)
                distance = entry_price - stop_loss
                target = entry_price + (self.RISK_REWARD_RATIO * distance)
            else:  # SELL
                stop_loss = entry_price + (self.ATR_STOP_MULTIPLIER * atr)
                distance = stop_loss - entry_price
                target = entry_price - (self.RISK_REWARD_RATIO * distance)
            
            logger.info(f"{direction} Risk: Entry={entry_price:.2f}, "
                       f"Stop={stop_loss:.2f}, Target={target:.2f}, "
                       f"ATR={atr:.2f}, R:R={self.RISK_REWARD_RATIO}")
            
            return round(stop_loss, 2), round(target, 2)
            
        except Exception as e:
            logger.error(f"Error calculating risk: {e}")
            # Safe fallback
            if direction == "BUY":
                return entry_price * 0.98, entry_price * 1.03
            else:
                return entry_price * 1.02, entry_price * 0.97
    
    def run_analysis_cycle(self, nifty_df: pd.DataFrame, stock_df: pd.DataFrame, 
                          symbol: str, bot_start_time: Optional[datetime] = None) -> Dict:
        """
        Main analysis cycle - orchestrates the entire strategy logic.
        
        Workflow:
        1. Calculate DR from first N minutes after bot start (or first N minutes of data)
        2. Calculate indicators
        3. Check regime
        4. Check trigger
        5. Calculate risk if signal found
        
        Args:
            nifty_df: NIFTY 50 DataFrame (OHLCV)
            stock_df: Stock DataFrame (OHLCV)
            symbol: Stock symbol
            bot_start_time: Optional bot start timestamp (for DR calculation)
            
        Returns:
            Decision dictionary with keys:
            - 'signal': "BUY", "SELL", or "NONE"
            - 'regime': Current market regime
            - 'entry_price': Entry price (if signal)
            - 'stop_loss': Stop loss price (if signal)
            - 'target': Target price (if signal)
            - 'dr_high': Defining range high
            - 'dr_low': Defining range low
        """
        logger.info(f"[{symbol}] === ANALYSIS CYCLE START ===")
        
        try:
            # Step 1: Load or calculate Defining Range
            state = self.get_bot_state(symbol)
            dr_high = state.get('dr_high')
            dr_low = state.get('dr_low')
            
            # Calculate DR if not present
            if dr_high is None or dr_low is None:
                logger.info(f"[{symbol}] DR not found, calculating from data...")
                dr_high, dr_low = self.get_defining_range(stock_df, bot_start_time)
                if dr_high is None or dr_low is None:
                    logger.warning(f"[{symbol}] Could not calculate DR, insufficient data")
                    return {
                        'signal': 'NONE',
                        'regime': 'NEUTRAL',
                        'message': 'Insufficient data for Defining Range calculation'
                    }
                
                # Save to Firestore
                self.save_bot_state(symbol, {
                    'dr_high': float(dr_high),
                    'dr_low': float(dr_low)
                })
            
            # Step 2: Calculate indicators
            nifty_df = self.calculate_indicators(nifty_df)
            stock_df = self.calculate_indicators(stock_df)
            
            # Step 3: Check regime
            regime = self.check_regime(nifty_df, stock_df)
            
            # Save regime to state
            self.save_bot_state(symbol, {'regime': regime})
            
            # Step 4: Check for trigger
            signal = self.check_trigger(stock_df, regime, dr_high, dr_low)
            
            # Step 5: If signal found, calculate risk
            if signal in ["BUY", "SELL"]:
                entry_price = stock_df.iloc[-1]['close']
                stop_loss, target = self.calculate_risk(entry_price, signal, stock_df)
                
                logger.info(f"[{symbol}] === SIGNAL GENERATED: {signal} ===")
                
                return {
                    'action': signal,  # Changed from 'signal' to 'action' for consistency
                    'signal': signal,  # Keep for backward compatibility
                    'regime': regime,
                    'entry_price': round(entry_price, 2),
                    'stop_loss': stop_loss,
                    'target': target,
                    'dr_high': round(dr_high, 2),
                    'dr_low': round(dr_low, 2),
                    'atr': round(stock_df.iloc[-1].get('atr', 0), 2),
                    'rsi': round(stock_df.iloc[-1].get('rsi', 50), 2),
                    'score': 75.0,  # Default Ironclad score (can be refined)
                    'timestamp': datetime.now(self.ist_tz).isoformat(),
                    # NEW: Fields for 30-Point Checklist compatibility
                    'breakout_direction': 'up' if signal == 'BUY' else 'down',
                    'pattern_name': f'Ironclad DR Breakout ({signal})',
                    'initial_stop_loss': stop_loss,
                    'calculated_price_target': target,
                }
            else:
                logger.info(f"[{symbol}] No trigger. Regime={regime}, Signal={signal}")
                
                return {
                    'signal': 'NONE',
                    'regime': regime,
                    'dr_high': round(dr_high, 2),
                    'dr_low': round(dr_low, 2),
                    'current_price': round(stock_df.iloc[-1]['close'], 2),
                    'message': f'No trigger conditions met (Regime: {regime})'
                }
        
        except Exception as e:
            logger.error(f"[{symbol}] Error in analysis cycle: {e}", exc_info=True)
            return {
                'signal': 'ERROR',
                'regime': 'NEUTRAL',
                'message': f'Analysis error: {str(e)}'
            }
