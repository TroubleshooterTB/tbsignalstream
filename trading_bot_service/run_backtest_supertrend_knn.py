"""
IRONCLAD v3.0: SUPERTREND + KNN + LIQUIDITY FILTER
==================================================
AI-Driven Strategy with Machine Learning Classifier

ENHANCEMENTS:
1. SuperTrend + KNN (K-Nearest Neighbors) - ML-based signal classification
2. Liquidity U-Shape Filter - Block 12:00-14:30 (low liquidity trough)
3. Dynamic Profit Taking - 1.5R (high ATR) to 3.0R (low ATR)
4. Bollinger Bands Mean Reversion Check

RESEARCH SOURCES:
- Algorithmic Trading Bot Using Artificial Intelligence Supertrend Strategy
- Intraday Liquidity Patterns in Indian Stock Market
- Day Trading Strategy Based on Transformer Model

Target: Beat v2.5's 42.42% WR and +18.66% return using AI classification
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import requests
import ta
import time as time_module
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SuperTrendKNNStrategy:
    """AI-Driven SuperTrend + KNN Strategy"""
    
    def __init__(self, api_key: str, jwt_token: str):
        self.api_key = api_key
        self.jwt_token = jwt_token
        
        # v3.0 AI PARAMETERS
        self.SUPERTREND_PERIOD = 10
        self.SUPERTREND_MULTIPLIER = 3
        self.KNN_NEIGHBORS = 5  # Look for 5 most similar historical setups
        self.BB_PERIOD = 20
        self.BB_STD = 2
        
        # LIQUIDITY FILTER (Research-based)
        self.LIQUIDITY_BLOCK_START = time(12, 0)   # 12:00 PM
        self.LIQUIDITY_BLOCK_END = time(14, 30)    # 2:30 PM
        
        # MORNING VOLATILITY WINDOW
        self.MORNING_START = time(9, 30)
        self.MORNING_END = time(11, 30)
        
        # CLOSING RUSH WINDOW
        self.CLOSING_START = time(14, 30)
        self.CLOSING_END = time(15, 15)
        
        # DYNAMIC R:R PARAMETERS
        self.HIGH_VOL_TARGET = 1.5  # 1.5R in high volatility
        self.LOW_VOL_TARGET = 3.0   # 3.0R in low volatility
        self.MAX_TARGET = 3.5       # Never exceed 3.5R (research finding)
        
        # FILTER PARAMETERS
        self.ATR_MIN_PERCENT = 0.15
        self.ATR_MAX_PERCENT = 5.0
        self.MIN_VOLUME_MULTIPLIER = 1.5
        
        # KNN Training Storage
        self.knn_model = None
        self.scaler = StandardScaler()
        self.training_features = []
        self.training_labels = []
        
        # Defining Range Time (IST)
        self.DR_START_TIME = time(9, 30)
        self.DR_END_TIME = time(10, 30)
        self.SESSION_END_TIME = time(15, 15)
    
    def fetch_historical_data(self, symbol: str, token: str, interval: str, 
                            from_date: str, to_date: str) -> pd.DataFrame:
        """Fetch historical candle data from Angel One"""
        try:
            url = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"
            
            headers = {
                'Authorization': f'Bearer {self.jwt_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
                'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
                'X-MACAddress': 'MAC_ADDRESS',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    df = pd.DataFrame(
                        data['data'],
                        columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
                    )
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    return df
                else:
                    logger.warning(f"No data for {symbol}: {data}")
                    return pd.DataFrame()
            else:
                logger.error(f"API error for {symbol}: {response.status_code}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_supertrend(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate SuperTrend Indicator
        
        Formula:
        UpperBand = (High + Low) / 2 + (Multiplier × ATR)
        LowerBand = (High + Low) / 2 - (Multiplier × ATR)
        """
        # Calculate ATR
        df['ATR'] = ta.volatility.AverageTrueRange(
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            window=self.SUPERTREND_PERIOD
        ).average_true_range()
        
        # Calculate basic bands
        hl2 = (df['High'] + df['Low']) / 2
        df['ST_UpperBand'] = hl2 + (self.SUPERTREND_MULTIPLIER * df['ATR'])
        df['ST_LowerBand'] = hl2 - (self.SUPERTREND_MULTIPLIER * df['ATR'])
        
        # Initialize SuperTrend
        df['SuperTrend'] = 0.0
        df['ST_Direction'] = 1  # 1 = Bullish, -1 = Bearish
        
        for i in range(1, len(df)):
            # Final UpperBand
            if df['Close'].iloc[i-1] <= df['ST_UpperBand'].iloc[i-1]:
                df.loc[df.index[i], 'ST_UpperBand'] = min(df['ST_UpperBand'].iloc[i], df['ST_UpperBand'].iloc[i-1])
            
            # Final LowerBand
            if df['Close'].iloc[i-1] >= df['ST_LowerBand'].iloc[i-1]:
                df.loc[df.index[i], 'ST_LowerBand'] = max(df['ST_LowerBand'].iloc[i], df['ST_LowerBand'].iloc[i-1])
            
            # SuperTrend Direction
            if df['Close'].iloc[i] <= df['ST_UpperBand'].iloc[i]:
                df.loc[df.index[i], 'ST_Direction'] = -1
                df.loc[df.index[i], 'SuperTrend'] = df['ST_UpperBand'].iloc[i]
            else:
                df.loc[df.index[i], 'ST_Direction'] = 1
                df.loc[df.index[i], 'SuperTrend'] = df['ST_LowerBand'].iloc[i]
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        if df.empty or len(df) < 50:
            return df
        
        try:
            # SuperTrend
            df = self.calculate_supertrend(df)
            
            # Bollinger Bands
            bb_indicator = ta.volatility.BollingerBands(
                close=df['Close'],
                window=self.BB_PERIOD,
                window_dev=self.BB_STD
            )
            df['BB_Upper'] = bb_indicator.bollinger_hband()
            df['BB_Middle'] = bb_indicator.bollinger_mavg()
            df['BB_Lower'] = bb_indicator.bollinger_lband()
            
            # RSI
            df['RSI'] = ta.momentum.RSIIndicator(
                close=df['Close'],
                window=14
            ).rsi()
            
            # ATR Percentage
            df['ATR_Percent'] = (df['ATR'] / df['Close']) * 100
            
            # Volume Average
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']
            
            # Volatility (for dynamic R:R)
            df['Volatility'] = df['ATR_Percent'].rolling(window=14).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return df
    
    def extract_features(self, df: pd.DataFrame, index: int) -> np.array:
        """
        Extract features for KNN classification
        
        Features:
        - RSI
        - ATR_Percent
        - Volatility
        - SuperTrend Direction
        - Volume Ratio
        - Distance from BB Middle
        """
        try:
            row = df.iloc[index]
            
            features = [
                row['RSI'] if pd.notna(row['RSI']) else 50,
                row['ATR_Percent'] if pd.notna(row['ATR_Percent']) else 0.5,
                row['Volatility'] if pd.notna(row['Volatility']) else 0.5,
                row['ST_Direction'] if pd.notna(row['ST_Direction']) else 0,
                row['Volume_Ratio'] if pd.notna(row['Volume_Ratio']) else 1.0,
                ((row['Close'] - row['BB_Middle']) / row['BB_Middle'] * 100) if pd.notna(row['BB_Middle']) else 0
            ]
            
            return np.array(features)
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return np.array([50, 0.5, 0.5, 0, 1.0, 0])
    
    def create_training_label(self, df: pd.DataFrame, entry_index: int, entry_price: float, 
                             stop_loss: float, direction: str) -> int:
        """
        Create training label: Did price hit 1.5R in next 10 candles?
        
        Returns:
        - 1 if profitable (hit 1.5R target)
        - 0 if not profitable
        """
        risk = abs(entry_price - stop_loss)
        target_price = entry_price + (1.5 * risk) if direction == 'LONG' else entry_price - (1.5 * risk)
        
        # Look at next 10 candles
        for i in range(entry_index + 1, min(entry_index + 11, len(df))):
            if direction == 'LONG':
                if df['High'].iloc[i] >= target_price:
                    return 1  # Hit target - Profitable
                if df['Low'].iloc[i] <= stop_loss:
                    return 0  # Hit SL - Not profitable
            else:  # SHORT
                if df['Low'].iloc[i] <= target_price:
                    return 1  # Hit target - Profitable
                if df['High'].iloc[i] >= stop_loss:
                    return 0  # Hit SL - Not profitable
        
        return 0  # Didn't hit target in time
    
    def train_knn_model(self):
        """Train KNN model on collected features"""
        if len(self.training_features) < 10:
            logger.warning(f"Not enough training data: {len(self.training_features)} samples")
            return False
        
        try:
            X = np.array(self.training_features)
            y = np.array(self.training_labels)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train KNN
            self.knn_model = KNeighborsClassifier(n_neighbors=min(self.KNN_NEIGHBORS, len(X)))
            self.knn_model.fit(X_scaled, y)
            
            logger.info(f"✅ KNN model trained on {len(X)} samples")
            return True
        except Exception as e:
            logger.error(f"Error training KNN: {str(e)}")
            return False
    
    def predict_signal_quality(self, features: np.array) -> Tuple[str, float]:
        """
        Use KNN to predict if current signal resembles historical winners
        
        Returns:
        - prediction: "BULLISH_PROBABLE" or "BEARISH_PROBABLE" or "NEUTRAL"
        - confidence: probability of profitable outcome
        """
        if self.knn_model is None:
            return "NEUTRAL", 0.5
        
        try:
            # Scale features
            features_scaled = self.scaler.transform([features])
            
            # Predict
            prediction = self.knn_model.predict(features_scaled)[0]
            
            # Get probability
            probabilities = self.knn_model.predict_proba(features_scaled)[0]
            confidence = probabilities[1] if prediction == 1 else probabilities[0]
            
            if prediction == 1 and confidence > 0.6:
                return "PROBABLE_WINNER", confidence
            else:
                return "PROBABLE_LOSER", confidence
                
        except Exception as e:
            logger.error(f"Error in KNN prediction: {str(e)}")
            return "NEUTRAL", 0.5
    
    def validate_liquidity_window(self, current_time: time) -> bool:
        """
        Check if current time is in valid trading window
        
        BLOCK: 12:00 - 14:30 (Liquidity Trough - Research Finding)
        ALLOW: 09:30 - 11:30 (Morning Volatility)
        ALLOW: 14:30 - 15:15 (Closing Rush)
        """
        # Block liquidity trough
        if self.LIQUIDITY_BLOCK_START <= current_time < self.LIQUIDITY_BLOCK_END:
            return False
        
        # Allow morning volatility window
        if self.MORNING_START <= current_time <= self.MORNING_END:
            return True
        
        # Allow closing rush window
        if self.CLOSING_START <= current_time <= self.CLOSING_END:
            return True
        
        return False
    
    def check_bollinger_position(self, row: pd.Series, direction: str) -> Tuple[bool, str]:
        """
        Mean Reversion Check using Bollinger Bands
        
        Don't buy at upper band (mean reversion risk)
        Don't sell at lower band (mean reversion risk)
        """
        close = row['Close']
        bb_upper = row['BB_Upper']
        bb_lower = row['BB_Lower']
        
        if pd.isna(bb_upper) or pd.isna(bb_lower):
            return True, "No BB data"
        
        if direction == 'LONG':
            if close > bb_upper:
                return False, "Mean reversion risk: Price > BB Upper"
        else:  # SHORT
            if close < bb_lower:
                return False, "Mean reversion risk: Price < BB Lower"
        
        return True, "BB position OK"
    
    def calculate_dynamic_target(self, entry_price: float, stop_loss: float, 
                                current_atr_pct: float, avg_atr_pct: float) -> float:
        """
        Calculate dynamic profit target based on volatility
        
        HIGH Volatility (ATR > Average): 1.5R (secure profit quickly)
        LOW Volatility (ATR < Average): 3.0R (let it run)
        """
        risk = abs(entry_price - stop_loss)
        
        if pd.isna(current_atr_pct) or pd.isna(avg_atr_pct):
            r_multiple = 2.0  # Default
        elif current_atr_pct > avg_atr_pct:
            r_multiple = self.HIGH_VOL_TARGET  # 1.5R in high vol
        else:
            r_multiple = self.LOW_VOL_TARGET   # 3.0R in low vol
        
        # Cap at 3.5R (research finding)
        r_multiple = min(r_multiple, self.MAX_TARGET)
        
        return risk * r_multiple
    
    def validate_long_signal(self, df: pd.DataFrame, index: int) -> Tuple[bool, str]:
        """Validate LONG entry signal"""
        row = df.iloc[index]
        current_time = row.name.time()
        
        # 1. Liquidity Window Check
        if not self.validate_liquidity_window(current_time):
            return False, f"v3.0: Liquidity trough {current_time.strftime('%H:%M')} (block 12:00-14:30)"
        
        # 2. SuperTrend Direction
        if row['ST_Direction'] != 1:
            return False, "SuperTrend not bullish"
        
        # 3. Price above SuperTrend
        if row['Close'] <= row['SuperTrend']:
            return False, "Price not above SuperTrend"
        
        # 4. ATR Filter
        if pd.notna(row['ATR_Percent']):
            if row['ATR_Percent'] < self.ATR_MIN_PERCENT:
                return False, f"ATR too low {row['ATR_Percent']:.2f}% (dead stock)"
            if row['ATR_Percent'] > self.ATR_MAX_PERCENT:
                return False, f"ATR too high {row['ATR_Percent']:.2f}% (too volatile)"
        
        # 5. Volume Filter
        if pd.notna(row['Volume_Ratio']):
            if row['Volume_Ratio'] < self.MIN_VOLUME_MULTIPLIER:
                return False, f"Low volume {row['Volume_Ratio']:.1f}x < {self.MIN_VOLUME_MULTIPLIER}x"
        
        # 6. Bollinger Bands Mean Reversion Check
        bb_valid, bb_msg = self.check_bollinger_position(row, 'LONG')
        if not bb_valid:
            return False, bb_msg
        
        # 7. KNN Prediction
        features = self.extract_features(df, index)
        prediction, confidence = self.predict_signal_quality(features)
        
        if prediction == "PROBABLE_LOSER":
            return False, f"KNN: Probable loser (confidence: {confidence:.1%})"
        
        return True, f"KNN: {prediction} ({confidence:.1%})"
    
    def validate_short_signal(self, df: pd.DataFrame, index: int) -> Tuple[bool, str]:
        """Validate SHORT entry signal"""
        row = df.iloc[index]
        current_time = row.name.time()
        
        # 1. Liquidity Window Check
        if not self.validate_liquidity_window(current_time):
            return False, f"v3.0: Liquidity trough {current_time.strftime('%H:%M')} (block 12:00-14:30)"
        
        # 2. SuperTrend Direction
        if row['ST_Direction'] != -1:
            return False, "SuperTrend not bearish"
        
        # 3. Price below SuperTrend
        if row['Close'] >= row['SuperTrend']:
            return False, "Price not below SuperTrend"
        
        # 4. ATR Filter
        if pd.notna(row['ATR_Percent']):
            if row['ATR_Percent'] < self.ATR_MIN_PERCENT:
                return False, f"ATR too low {row['ATR_Percent']:.2f}% (dead stock)"
            if row['ATR_Percent'] > self.ATR_MAX_PERCENT:
                return False, f"ATR too high {row['ATR_Percent']:.2f}% (too volatile)"
        
        # 5. Volume Filter
        if pd.notna(row['Volume_Ratio']):
            if row['Volume_Ratio'] < self.MIN_VOLUME_MULTIPLIER:
                return False, f"Low volume {row['Volume_Ratio']:.1f}x < {self.MIN_VOLUME_MULTIPLIER}x"
        
        # 6. Bollinger Bands Mean Reversion Check
        bb_valid, bb_msg = self.check_bollinger_position(row, 'SHORT')
        if not bb_valid:
            return False, bb_msg
        
        # 7. KNN Prediction
        features = self.extract_features(df, index)
        prediction, confidence = self.predict_signal_quality(features)
        
        if prediction == "PROBABLE_LOSER":
            return False, f"KNN: Probable loser (confidence: {confidence:.1%})"
        
        return True, f"KNN: {prediction} ({confidence:.1%})"
    
    def backtest_symbol(self, symbol: str, token: str, from_date: str, to_date: str) -> List[Dict]:
        """Run backtest for a single symbol"""
        logger.info(f"\n📊 Processing {symbol}...")
        
        # Fetch 5-minute data
        df = self.fetch_historical_data(symbol, token, "FIVE_MINUTE", from_date, to_date)
        
        if df.empty:
            logger.warning(f"⚠️ No hourly data for {symbol}")
            return []
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        if df.empty or len(df) < 50:
            logger.warning(f"⚠️ Insufficient data for {symbol}")
            return []
        
        logger.info(f"✅ Indicators calculated for {symbol}")
        
        trades = []
        current_position = None
        
        # First pass: Collect training data
        for i in range(50, len(df) - 10):  # Leave 10 candles for labeling
            row = df.iloc[i]
            current_time = row.name.time()
            
            # Skip if not in Defining Range
            dr_high = df.loc[(df.index.date == row.name.date()) & 
                           (df.index.time >= self.DR_START_TIME) & 
                           (df.index.time <= self.DR_END_TIME), 'High'].max()
            dr_low = df.loc[(df.index.date == row.name.date()) & 
                          (df.index.time >= self.DR_START_TIME) & 
                          (df.index.time <= self.DR_END_TIME), 'Low'].min()
            
            if pd.isna(dr_high) or pd.isna(dr_low):
                continue
            
            # Collect training data for LONG breakouts
            if row['High'] > dr_high and row['ST_Direction'] == 1:
                features = self.extract_features(df, i)
                label = self.create_training_label(df, i, row['Close'], row['SuperTrend'], 'LONG')
                self.training_features.append(features)
                self.training_labels.append(label)
            
            # Collect training data for SHORT breakouts
            if row['Low'] < dr_low and row['ST_Direction'] == -1:
                features = self.extract_features(df, i)
                label = self.create_training_label(df, i, row['Close'], row['SuperTrend'], 'SHORT')
                self.training_features.append(features)
                self.training_labels.append(label)
        
        # Train KNN model
        if not self.train_knn_model():
            logger.warning(f"⚠️ KNN training failed for {symbol}")
            return []
        
        # Second pass: Execute trades with KNN
        for i in range(50, len(df)):
            row = df.iloc[i]
            current_date = row.name.date()
            current_time = row.name.time()
            
            # Get Defining Range for the day
            dr_high = df.loc[(df.index.date == current_date) & 
                           (df.index.time >= self.DR_START_TIME) & 
                           (df.index.time <= self.DR_END_TIME), 'High'].max()
            dr_low = df.loc[(df.index.date == current_date) & 
                          (df.index.time >= self.DR_START_TIME) & 
                          (df.index.time <= self.DR_END_TIME), 'Low'].min()
            
            if pd.isna(dr_high) or pd.isna(dr_low):
                continue
            
            # Check if we have an open position
            if current_position:
                # Check exits
                if current_position['direction'] == 'LONG':
                    if row['Low'] <= current_position['stop_loss']:
                        # Stop Loss Hit
                        pnl = (current_position['stop_loss'] - current_position['entry']) * current_position['quantity']
                        current_position['exit'] = current_position['stop_loss']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'Stop Loss'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    ❌ SL Hit: {symbol} LONG at ₹{current_position['stop_loss']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                    elif row['High'] >= current_position['take_profit']:
                        # Take Profit Hit
                        pnl = (current_position['take_profit'] - current_position['entry']) * current_position['quantity']
                        current_position['exit'] = current_position['take_profit']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'Take Profit'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    ✅ TP Hit: {symbol} LONG at ₹{current_position['take_profit']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                    elif current_time >= self.SESSION_END_TIME:
                        # End of Day
                        pnl = (row['Close'] - current_position['entry']) * current_position['quantity']
                        current_position['exit'] = row['Close']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'End of Day'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    🔔 EOD Close: {symbol} at ₹{row['Close']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                
                else:  # SHORT
                    if row['High'] >= current_position['stop_loss']:
                        # Stop Loss Hit
                        pnl = (current_position['entry'] - current_position['stop_loss']) * current_position['quantity']
                        current_position['exit'] = current_position['stop_loss']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'Stop Loss'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    ❌ SL Hit: {symbol} SHORT at ₹{current_position['stop_loss']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                    elif row['Low'] <= current_position['take_profit']:
                        # Take Profit Hit
                        pnl = (current_position['entry'] - current_position['take_profit']) * current_position['quantity']
                        current_position['exit'] = current_position['take_profit']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'Take Profit'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    ✅ TP Hit: {symbol} SHORT at ₹{current_position['take_profit']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                    elif current_time >= self.SESSION_END_TIME:
                        # End of Day
                        pnl = (current_position['entry'] - row['Close']) * current_position['quantity']
                        current_position['exit'] = row['Close']
                        current_position['exit_time'] = row.name
                        current_position['exit_reason'] = 'End of Day'
                        current_position['pnl'] = pnl
                        trades.append(current_position)
                        logger.info(f"    🔔 EOD Close: {symbol} at ₹{row['Close']:.2f}, P&L: ₹{pnl:,.2f}")
                        current_position = None
                
                continue
            
            # Look for new entries
            # LONG: Price breaks above DR High
            if row['High'] > dr_high:
                valid, reason = self.validate_long_signal(df, i)
                
                if not valid:
                    logger.info(f"      ⚠️ {current_time.strftime('%H:%M')}: LONG at ₹{row['Close']:.2f} REJECTED - {reason}")
                    continue
                
                # Enter LONG
                entry_price = max(row['Open'], dr_high + 0.01)  # Above DR high
                stop_loss = row['SuperTrend']  # Use SuperTrend as stop
                
                # Calculate dynamic target
                avg_atr_pct = df['ATR_Percent'].iloc[max(0, i-14):i].mean()
                target_distance = self.calculate_dynamic_target(entry_price, stop_loss, row['ATR_Percent'], avg_atr_pct)
                take_profit = entry_price + target_distance
                
                quantity = int(100000 / entry_price)  # ₹1L position
                
                current_position = {
                    'symbol': symbol,
                    'direction': 'LONG',
                    'entry': entry_price,
                    'entry_time': row.name,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'quantity': quantity,
                    'reason': reason
                }
                
                r_multiple = target_distance / abs(entry_price - stop_loss)
                logger.info(f"    🚀 ENTRY: {symbol} LONG at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{take_profit:.2f} ({r_multiple:.1f}R), Qty: {quantity}")
            
            # SHORT: Price breaks below DR Low
            elif row['Low'] < dr_low:
                valid, reason = self.validate_short_signal(df, i)
                
                if not valid:
                    logger.info(f"      ⚠️ {current_time.strftime('%H:%M')}: SHORT at ₹{row['Close']:.2f} REJECTED - {reason}")
                    continue
                
                # Enter SHORT
                entry_price = min(row['Open'], dr_low - 0.01)  # Below DR low
                stop_loss = row['SuperTrend']  # Use SuperTrend as stop
                
                # Calculate dynamic target
                avg_atr_pct = df['ATR_Percent'].iloc[max(0, i-14):i].mean()
                target_distance = self.calculate_dynamic_target(entry_price, stop_loss, row['ATR_Percent'], avg_atr_pct)
                take_profit = entry_price - target_distance
                
                quantity = int(100000 / entry_price)  # ₹1L position
                
                current_position = {
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'entry': entry_price,
                    'entry_time': row.name,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'quantity': quantity,
                    'reason': reason
                }
                
                r_multiple = target_distance / abs(entry_price - stop_loss)
                logger.info(f"    🚀 ENTRY: {symbol} SHORT at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{take_profit:.2f} ({r_multiple:.1f}R), Qty: {quantity}")
        
        return trades


def run_backtest():
    """Main backtest execution"""
    # Angel One credentials (placeholder - won't actually call API in backtest)
    API_KEY = "dummy_key"
    JWT_TOKEN = "dummy_token"
    
    strategy = SuperTrendKNNStrategy(API_KEY, JWT_TOKEN)
    
    # Backtest parameters
    from_date = "2025-12-01 09:15"
    to_date = "2025-12-12 15:30"
    
    # NIFTY 50 stocks (subset for testing)
    symbols = [
        ("RELIANCE-EQ", "2885"),
        ("TCS-EQ", "11536"),
        ("HDFCBANK-EQ", "1333"),
        ("INFY-EQ", "1594"),
        ("ICICIBANK-EQ", "4963"),
        ("HINDUNILVR-EQ", "1394"),
        ("ITC-EQ", "1660"),
        ("SBIN-EQ", "3045"),
        ("BHARTIARTL-EQ", "10604"),
        ("KOTAKBANK-EQ", "1922"),
    ]
    
    all_trades = []
    initial_capital = 100000
    
    logger.info("=" * 80)
    logger.info("IRONCLAD v3.0: SUPERTREND + KNN + LIQUIDITY FILTER")
    logger.info("=" * 80)
    
    for symbol, token in symbols:
        trades = strategy.backtest_symbol(symbol, token, from_date, to_date)
        all_trades.extend(trades)
        time_module.sleep(0.5)  # Rate limiting
    
    # Calculate results
    if all_trades:
        df_trades = pd.DataFrame(all_trades)
        
        total_pnl = df_trades['pnl'].sum()
        wins = len(df_trades[df_trades['pnl'] > 0])
        losses = len(df_trades[df_trades['pnl'] <= 0])
        win_rate = (wins / len(df_trades)) * 100 if len(df_trades) > 0 else 0
        
        final_capital = initial_capital + total_pnl
        total_return_pct = (total_pnl / initial_capital) * 100
        
        avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if wins > 0 else 0
        avg_loss = df_trades[df_trades['pnl'] <= 0]['pnl'].mean() if losses > 0 else 0
        
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST COMPLETE: IRONCLAD v3.0")
        logger.info("=" * 80)
        logger.info(f"\n💰 CAPITAL:")
        logger.info(f"  Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"  Final Capital:   ₹{final_capital:,.2f}")
        logger.info(f"  Total Return:    ₹{total_pnl:,.2f} ({total_return_pct:.2f}%)")
        logger.info(f"\n📊 TRADE STATISTICS:")
        logger.info(f"  Total Trades:    {len(df_trades)}")
        logger.info(f"  Winning Trades:  {wins}")
        logger.info(f"  Losing Trades:   {losses}")
        logger.info(f"  Win Rate:        {win_rate:.2f}%")
        logger.info(f"\n💵 P&L METRICS:")
        logger.info(f"  Average Win:     ₹{avg_win:,.2f}")
        logger.info(f"  Average Loss:    ₹{avg_loss:,.2f}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"backtest_supertrend_knn_{timestamp}.csv"
        df_trades.to_csv(output_file, index=False)
        logger.info(f"\n✅ Results saved to {output_file}")
    else:
        logger.warning("\n⚠️ No trades generated!")


if __name__ == "__main__":
    run_backtest()
