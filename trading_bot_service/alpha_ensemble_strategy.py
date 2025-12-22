"""
The Alpha-Ensemble Strategy
Implements retest-based entries with market regime filtering
Designed to achieve 40%+ win rate with 2.5:1 R:R
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import logging
import requests
import time as time_module
from typing import List, Dict, Tuple, Optional
import ta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AlphaEnsembleStrategy:
    """Alpha-Ensemble Strategy with Market Regime & Retest Logic"""
    
    def __init__(self, api_key: str, jwt_token: str, strategy_params: Optional[Dict] = None):
        self.api_key = api_key
        self.jwt_token = jwt_token
        
        # Load strategy parameters (use provided params or optimized defaults)
        params = strategy_params or {}
        
        # ===== LAYER 1: MARKET REGIME FILTERS =====
        self.NIFTY_ALIGNMENT_THRESHOLD = params.get('nifty_alignment', 0.0)  # Same direction = 0.0%
        self.VIX_MAX_THRESHOLD = params.get('vix_max', 22.0)
        
        # ===== LAYER 2: TREND & RETEST LOGIC =====
        self.EMA_200_PERIOD = 200
        self.EMA_20_PERIOD = 20
        self.VWAP_RETEST_TOLERANCE = 0.1
        
        # ===== LAYER 3: EXECUTION FILTERS (USER-OPTIMIZED) =====
        self.ADX_MIN_TRENDING = params.get('adx_threshold', 25)
        self.ADX_PERIOD = 14
        self.VOLUME_MULTIPLIER = params.get('volume_multiplier', 2.5)
        self.RSI_PERIOD = 14
        
        # RSI Sweet Spots (USER-OPTIMIZED)
        rsi_oversold = params.get('rsi_oversold', 35)
        rsi_overbought = params.get('rsi_overbought', 70)
        self.RSI_LONG_MIN = rsi_oversold  # LONG: RSI 35-70
        self.RSI_LONG_MAX = rsi_overbought
        self.RSI_SHORT_MIN = 100 - rsi_overbought  # SHORT: RSI 30-65 (inverted)
        self.RSI_SHORT_MAX = 100 - rsi_oversold
        
        # Distance from EMA
        self.MAX_DISTANCE_FROM_50EMA = 1.5
        
        # ATR Window
        self.ATR_MIN_PERCENT = 0.15
        self.ATR_MAX_PERCENT = 4.0
        self.ATR_PERIOD = 14
        
        # ===== POSITION & RISK MANAGEMENT (USER-OPTIMIZED) =====
        self.RISK_REWARD_RATIO = params.get('risk_reward', 2.5)  # 1:2.5 R:R
        self.ATR_MULTIPLIER_FOR_SL = 1.8
        self.MAXIMUM_SL_PERCENT = 0.6
        self.RISK_PER_TRADE_PERCENT = params.get('position_size', 5.0)  # 5% per trade
        self.BREAKEVEN_RATIO = 1.0
        
        # SuperTrend Exit
        self.SUPERTREND_PERIOD = 10
        self.SUPERTREND_MULTIPLIER = 3
        
        # ===== TIME FILTERS (USER-OPTIMIZED) =====
        trading_start = params.get('trading_start_hour', 10)  # 10:30 AM
        trading_end = params.get('trading_end_hour', 14)    # 14:15 PM
        self.SKIP_10AM_HOUR = (trading_start > 10)  # Skip if trading starts after 10 AM
        self.SKIP_11AM_HOUR = False  # Allow 11 AM hour (within 10:30-14:15)
        self.SKIP_LUNCH_HOUR = False  # Allow lunch hour (within 10:30-14:15)
        self.DR_START_TIME = time(9, 30)
        self.DR_END_TIME = time(10, 30)
        self.SESSION_START_TIME = time(trading_start, 30)  # 10:30 AM
        self.SESSION_END_TIME = time(trading_end, 15)  # 14:15 PM
        
        # ===== SYMBOL BLACKLIST =====
        self.BLACKLISTED_SYMBOLS = [
            'SBIN-EQ', 'POWERGRID-EQ', 'SHRIRAMFIN-EQ', 'JSWSTEEL-EQ'
        ]
        
        # Log loaded parameters
        logger.info(f"✅ Alpha-Ensemble Strategy Initialized with:")
        logger.info(f"   ADX Threshold: {self.ADX_MIN_TRENDING}")
        logger.info(f"   RSI Range LONG: {self.RSI_LONG_MIN}-{self.RSI_LONG_MAX}")
        logger.info(f"   RSI Range SHORT: {self.RSI_SHORT_MIN}-{self.RSI_SHORT_MAX}")
        logger.info(f"   Volume: {self.VOLUME_MULTIPLIER}x")
        logger.info(f"   R:R: 1:{self.RISK_REWARD_RATIO}")
        logger.info(f"   Position Size: {self.RISK_PER_TRADE_PERCENT}%")
        logger.info(f"   Trading Hours: {self.SESSION_START_TIME.strftime('%H:%M')}-{self.SESSION_END_TIME.strftime('%H:%M')}")
        logger.info(f"   Nifty Alignment: Same Direction ({self.NIFTY_ALIGNMENT_THRESHOLD}%)")
    
    def fetch_historical_data(self, symbol: str, token: str, interval: str, 
                            from_date: str, to_date: str) -> pd.DataFrame:
        """Fetch historical candle data from Angel One"""
        try:
            url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/historical/v1/getCandleData"
            
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
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            # Rate limiting: Small delay to avoid exceeding API limits (276 symbols in 15 min window)
            time_module.sleep(0.05)  # 50ms delay = ~14 seconds for 276 symbols (well within 15 min)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    df = pd.DataFrame(data['data'], 
                                    columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    df = df.astype(float)
                    return df
            
            logger.warning(f"Failed to fetch data for {symbol}: {response.text}")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate VWAP with daily reset"""
        data['Date'] = data.index.date
        
        def calc_vwap_group(group):
            typical_price = (group['High'] + group['Low'] + group['Close']) / 3
            vwap = (typical_price * group['Volume']).cumsum() / group['Volume'].cumsum()
            return vwap
        
        vwap_values = []
        for date, group in data.groupby('Date'):
            vwap = calc_vwap_group(group)
            vwap_values.append(vwap)
        
        data['VWAP'] = pd.concat(vwap_values)
        data.drop('Date', axis=1, inplace=True)
        
        return data
    
    def calculate_ema(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Calculate Exponential Moving Averages"""
        # Validate sufficient data for the largest EMA period
        max_period = max(periods) if periods else 200
        if len(data) < max_period:
            logging.warning(f"⚠️ Insufficient data for EMA calculation: {len(data)} < {max_period}")
            return None
        
        for period in periods:
            data[f'EMA_{period}'] = data['Close'].ewm(span=period, adjust=False).mean()
        return data
    
    def calculate_adx(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ADX (Average Directional Index)"""
        # Require minimum data points for ADX calculation (window + buffer)
        min_required = self.ADX_PERIOD + 10
        if len(data) < min_required:
            logging.warning(f"⚠️ Insufficient data for ADX calculation: {len(data)} < {min_required} candles")
            data['ADX'] = 0.0  # Set to 0 so filters will reject it
            return data
            
        adx_indicator = ta.trend.ADXIndicator(
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            window=self.ADX_PERIOD
        )
        data['ADX'] = adx_indicator.adx()
        return data
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate RSI"""
        # Validate sufficient data for RSI calculation
        if len(data) < self.RSI_PERIOD:
            logging.warning(f"⚠️ Insufficient data for RSI calculation: {len(data)} < {self.RSI_PERIOD}")
            return None
        
        data['RSI'] = ta.momentum.RSIIndicator(
            close=data['Close'],
            window=self.RSI_PERIOD
        ).rsi()
        return data
    
    def calculate_atr(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate ATR (Average True Range)"""
        # Validate sufficient data for ATR calculation
        if len(data) < self.ATR_PERIOD:
            logging.warning(f"⚠️ Insufficient data for ATR calculation: {len(data)} < {self.ATR_PERIOD}")
            return None
        
        data['ATR'] = ta.volatility.AverageTrueRange(
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            window=self.ATR_PERIOD
        ).average_true_range()
        return data
    
    def calculate_supertrend(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate SuperTrend indicator"""
        hl2 = (data['High'] + data['Low']) / 2
        data['ATR_ST'] = ta.volatility.AverageTrueRange(
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            window=self.SUPERTREND_PERIOD
        ).average_true_range()
        
        data['UpperBand'] = hl2 + (self.SUPERTREND_MULTIPLIER * data['ATR_ST'])
        data['LowerBand'] = hl2 - (self.SUPERTREND_MULTIPLIER * data['ATR_ST'])
        
        data['SuperTrend'] = 0.0
        data['SuperTrend_Direction'] = 0
        
        for i in range(1, len(data)):
            if data['Close'].iloc[i] > data['UpperBand'].iloc[i-1]:
                data.loc[data.index[i], 'SuperTrend'] = data['LowerBand'].iloc[i]
                data.loc[data.index[i], 'SuperTrend_Direction'] = 1
            elif data['Close'].iloc[i] < data['LowerBand'].iloc[i-1]:
                data.loc[data.index[i], 'SuperTrend'] = data['UpperBand'].iloc[i]
                data.loc[data.index[i], 'SuperTrend_Direction'] = -1
            else:
                data.loc[data.index[i], 'SuperTrend'] = data['SuperTrend'].iloc[i-1]
                data.loc[data.index[i], 'SuperTrend_Direction'] = data['SuperTrend_Direction'].iloc[i-1]
        
        return data
    
    def get_defining_range(self, data: pd.DataFrame, date) -> Optional[Dict]:
        """Get the defining range (9:30-10:30 AM)"""
        dr_data = data[
            (data.index.date == date) &
            (data.index.time >= self.DR_START_TIME) &
            (data.index.time < self.DR_END_TIME)
        ]
        
        if len(dr_data) == 0:
            return None
        
        return {
            'high': dr_data['High'].max(),
            'low': dr_data['Low'].min(),
            'end_time': dr_data.index[-1]
        }
    
    def check_market_regime(self, nifty_data: pd.DataFrame, date, trade_direction: str) -> Tuple[bool, str]:
        """
        LAYER 1: Check if market alignment and VIX conditions are met
        """
        # Get Nifty data for the day
        day_data = nifty_data[nifty_data.index.date == date]
        
        if len(day_data) == 0:
            return False, "No Nifty data for day"
        
        # Get 9:15 AM open price
        market_open = day_data.iloc[0]['Open']
        current_price = day_data.iloc[-1]['Close']
        
        nifty_change_pct = ((current_price - market_open) / market_open) * 100
        
        # Check Nifty alignment
        if trade_direction == 'LONG':
            if nifty_change_pct < self.NIFTY_ALIGNMENT_THRESHOLD:
                return False, f"Nifty not bullish: {nifty_change_pct:.2f}% < {self.NIFTY_ALIGNMENT_THRESHOLD}%"
        else:  # SHORT
            if nifty_change_pct > -self.NIFTY_ALIGNMENT_THRESHOLD:
                return False, f"Nifty not bearish: {nifty_change_pct:.2f}% > -{self.NIFTY_ALIGNMENT_THRESHOLD}%"
        
        # TODO: Add VIX check when VIX data is available
        # For now, we'll skip the VIX filter
        
        return True, f"Market aligned ({nifty_change_pct:+.2f}%)"
    
    def check_retest_entry(self, row: pd.DataFrame, prev_row: pd.DataFrame, 
                          dr_high: float, dr_low: float, trade_direction: str,
                          breakout_occurred: bool) -> Tuple[bool, str]:
        """
        LAYER 2: Check for retest entry (not direct breakout)
        
        Logic:
        1. Breakout must have occurred (close above/below DR)
        2. Price must pull back to VWAP or 20 EMA
        3. Price must stay above/below DR level during retest
        """
        if not breakout_occurred:
            return False, "No breakout yet"
        
        vwap = row['VWAP']
        ema_20 = row['EMA_20']
        close = row['Close']
        
        if trade_direction == 'LONG':
            # For LONG: Price pulled back to VWAP/EMA but stayed above DR High
            if close < dr_high:
                return False, "Price back below DR High (failed breakout)"
            
            # Check if touching VWAP or EMA_20 (within tolerance)
            distance_to_vwap = abs(close - vwap) / close * 100
            distance_to_ema = abs(close - ema_20) / close * 100
            
            if distance_to_vwap <= self.VWAP_RETEST_TOLERANCE:
                return True, f"VWAP retest at ₹{close:.2f} (dist: {distance_to_vwap:.2f}%)"
            elif distance_to_ema <= self.VWAP_RETEST_TOLERANCE:
                return True, f"EMA20 retest at ₹{close:.2f} (dist: {distance_to_ema:.2f}%)"
            
            return False, f"No retest (VWAP dist: {distance_to_vwap:.2f}%, EMA dist: {distance_to_ema:.2f}%)"
        
        else:  # SHORT
            # For SHORT: Price pulled back to VWAP/EMA but stayed below DR Low
            if close > dr_low:
                return False, "Price back above DR Low (failed breakout)"
            
            distance_to_vwap = abs(close - vwap) / close * 100
            distance_to_ema = abs(close - ema_20) / close * 100
            
            if distance_to_vwap <= self.VWAP_RETEST_TOLERANCE:
                return True, f"VWAP retest at ₹{close:.2f} (dist: {distance_to_vwap:.2f}%)"
            elif distance_to_ema <= self.VWAP_RETEST_TOLERANCE:
                return True, f"EMA20 retest at ₹{close:.2f} (dist: {distance_to_ema:.2f}%)"
            
            return False, f"No retest (VWAP dist: {distance_to_vwap:.2f}%, EMA dist: {distance_to_ema:.2f}%)"
    
    def check_execution_filters(self, row: pd.DataFrame, minute_data: pd.DataFrame, 
                               minute_idx: int, trade_direction: str,
                               ema_200_15m: float) -> Tuple[bool, str]:
        """
        LAYER 3: 5-Factor Execution Filters
        """
        close = row['Close']
        
        # Filter 1: 200 EMA Trend (15-minute)
        if trade_direction == 'LONG':
            if close < ema_200_15m:
                return False, f"Price below 200 EMA ({close:.2f} < {ema_200_15m:.2f})"
        else:  # SHORT
            if close > ema_200_15m:
                return False, f"Price above 200 EMA ({close:.2f} > {ema_200_15m:.2f})"
        
        # Filter 2: ADX > 25 (MANDATORY)
        adx = row['ADX']
        if pd.isna(adx) or adx < self.ADX_MIN_TRENDING:
            return False, f"ADX too low: {adx:.1f} < {self.ADX_MIN_TRENDING}"
        
        # Filter 3: Institutional Volume (2.5x)
        if minute_idx < 20:
            return False, "Not enough history for volume calculation"
        
        recent_volumes = minute_data.iloc[minute_idx-20:minute_idx]['Volume']
        avg_volume = recent_volumes.mean()
        current_volume = row['Volume']
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        if volume_ratio < self.VOLUME_MULTIPLIER:
            return False, f"Volume too low: {volume_ratio:.1f}x < {self.VOLUME_MULTIPLIER}x"
        
        # Filter 4: RSI Sweet Spot
        rsi = row['RSI']
        if trade_direction == 'LONG':
            if rsi < self.RSI_LONG_MIN or rsi > self.RSI_LONG_MAX:
                return False, f"RSI outside sweet spot: {rsi:.0f} (need {self.RSI_LONG_MIN}-{self.RSI_LONG_MAX})"
        else:  # SHORT
            if rsi < self.RSI_SHORT_MIN or rsi > self.RSI_SHORT_MAX:
                return False, f"RSI outside sweet spot: {rsi:.0f} (need {self.RSI_SHORT_MIN}-{self.RSI_SHORT_MAX})"
        
        # Filter 5: Distance from 50 EMA < 2%
        ema_50 = row['EMA_50']
        distance_from_ema = abs(close - ema_50) / close * 100
        if distance_from_ema > self.MAX_DISTANCE_FROM_50EMA:
            return False, f"Too far from 50 EMA: {distance_from_ema:.2f}% > {self.MAX_DISTANCE_FROM_50EMA}%"
        
        # Filter 6: ATR Window
        atr = row['ATR']
        atr_percent = (atr / close) * 100
        if atr_percent < self.ATR_MIN_PERCENT or atr_percent > self.ATR_MAX_PERCENT:
            return False, f"ATR outside range: {atr_percent:.2f}% (need {self.ATR_MIN_PERCENT}-{self.ATR_MAX_PERCENT}%)"
        
        return True, f"All filters passed [ADX={adx:.1f}, Vol={volume_ratio:.1f}x, RSI={rsi:.0f}, ATR={atr_percent:.2f}%]"
    
    def run_backtest(self, symbols: List[Dict], start_date: str, end_date: str, 
                    initial_capital: float = 100000) -> Dict:
        """
        Run backtest for Alpha-Ensemble Strategy
        """
        logger.info("=" * 80)
        logger.info("ALPHA-ENSEMBLE STRATEGY BACKTEST")
        logger.info("=" * 80)
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"Symbols: {len(symbols)}")
        logger.info("")
        
        capital = initial_capital
        trades = []
        
        # Fetch Nifty 50 data for market regime filter
        logger.info("📊 Fetching Nifty 50 data for market regime filter...")
        nifty_data = self.fetch_historical_data(
            'Nifty 50', '99926000', 'FIVE_MINUTE',
            start_date + " 09:15", end_date + " 15:30"
        )
        
        if nifty_data.empty:
            logger.error("❌ Failed to fetch Nifty data - cannot proceed")
            return {'trades': [], 'capital': capital}
        
        for symbol_info in symbols:
            symbol = symbol_info['symbol']
            token = symbol_info['token']
            
            # Skip blacklisted symbols
            if symbol in self.BLACKLISTED_SYMBOLS:
                logger.info(f"⚠️ {symbol} BLACKLISTED - skipping")
                continue
            
            logger.info(f"\n📊 Processing {symbol}...")
            time_module.sleep(2)
            
            # Fetch 15-minute data for 200 EMA trend filter
            ema_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=60)).strftime("%Y-%m-%d")
            data_15m = self.fetch_historical_data(
                symbol, token, "FIFTEEN_MINUTE",
                ema_start_date + " 09:15", end_date + " 15:30"
            )
            
            if data_15m.empty:
                logger.warning(f"⚠️ No 15-minute data for {symbol}")
                continue
            
            # Calculate 200 EMA on 15-minute chart
            data_15m = self.calculate_ema(data_15m, [200])
            if data_15m is None:
                logger.warning(f"⚠️ Skipping {symbol} - insufficient 15-min data for EMA200")
                continue
            
            # Fetch 5-minute data for execution
            minute_data = self.fetch_historical_data(
                symbol, token, "FIVE_MINUTE",
                start_date + " 09:15", end_date + " 15:30"
            )
            
            if minute_data.empty:
                logger.warning(f"⚠️ No 5-minute data for {symbol}")
                continue
            
            # Calculate all indicators on 5-minute data (check for None after each)
            minute_data = self.calculate_vwap(minute_data)
            
            minute_data = self.calculate_ema(minute_data, [20, 50])
            if minute_data is None:
                logger.warning(f"⚠️ Skipping {symbol} - insufficient 5-min data for EMA")
                continue
                
            minute_data = self.calculate_adx(minute_data)
            if minute_data is None:
                logger.warning(f"⚠️ Skipping {symbol} - insufficient data for ADX")
                continue
                
            minute_data = self.calculate_rsi(minute_data)
            if minute_data is None:
                logger.warning(f"⚠️ Skipping {symbol} - insufficient data for RSI")
                continue
                
            minute_data = self.calculate_atr(minute_data)
            if minute_data is None:
                logger.warning(f"⚠️ Skipping {symbol} - insufficient data for ATR")
                continue
                
            minute_data = self.calculate_supertrend(minute_data)
            
            logger.info(f"✅ Indicators calculated for {symbol}")
            
            # Iterate through each trading day
            trading_dates = sorted(set(minute_data.index.date))
            
            for date in trading_dates:
                # Get defining range
                dr = self.get_defining_range(minute_data, date)
                if dr is None:
                    continue
                
                # Get 200 EMA value from 15-minute chart
                ema_15m_data = data_15m[data_15m.index.date <= date]
                if len(ema_15m_data) == 0 or pd.isna(ema_15m_data.iloc[-1]['EMA_200']):
                    logger.info(f"    ⚠️ {date}: No 200 EMA data")
                    continue
                
                ema_200_15m = ema_15m_data.iloc[-1]['EMA_200']
                
                # Determine trend bias from 200 EMA
                day_close = minute_data[minute_data.index.date == date].iloc[-1]['Close']
                trend_bias = 'BULLISH' if day_close > ema_200_15m else 'BEARISH'
                
                logger.info(f"  📅 {date}: {trend_bias} bias (200 EMA: {ema_200_15m:.2f}), DR: {dr['low']:.2f} - {dr['high']:.2f}")
                
                # Get intraday data after defining range
                intraday_data = minute_data[
                    (minute_data.index.date == date) &
                    (minute_data.index > dr['end_time'])
                ]
                
                if len(intraday_data) == 0:
                    continue
                
                # Track breakout state and trade taken flag
                breakout_occurred = False
                breakout_type = None
                trade_taken_today = False  # CRITICAL: Prevent multiple trades per symbol per day
                
                # Scan for retest entries
                for idx in range(1, len(intraday_data)):
                    timestamp = intraday_data.index[idx]
                    row = intraday_data.iloc[idx]
                    prev_row = intraday_data.iloc[idx-1]
                    
                    # Skip hour blocks
                    current_hour = timestamp.hour
                    if (self.SKIP_10AM_HOUR and current_hour == 10) or \
                       (self.SKIP_11AM_HOUR and current_hour == 11) or \
                       (self.SKIP_LUNCH_HOUR and current_hour == 13):
                        continue
                    
                    # Check if breakout occurred (only during configured trading hours)
                    if not breakout_occurred and not trade_taken_today:  # Skip if trade already taken
                        # Skip new entries outside configured trading hours
                        current_time = timestamp.time()
                        if current_time < self.SESSION_START_TIME or current_time > self.SESSION_END_TIME:
                            continue  # Outside trading session for new entries
                        
                        if row['Close'] > dr['high'] and trend_bias == 'BULLISH':
                            breakout_occurred = True
                            breakout_type = 'LONG'
                            logger.info(f"      💥 {timestamp.strftime('%H:%M')}: Breakout detected (LONG at ₹{row['Close']:.2f})")
                            continue
                        elif row['Close'] < dr['low'] and trend_bias == 'BEARISH':
                            breakout_occurred = True
                            breakout_type = 'SHORT'
                            logger.info(f"      💥 {timestamp.strftime('%H:%M')}: Breakout detected (SHORT at ₹{row['Close']:.2f})")
                            continue
                    
                    # If breakout occurred, look for retest entry
                    if breakout_occurred and breakout_type and not trade_taken_today:  # Skip if trade already taken
                        # Skip new entries outside configured trading hours
                        current_time = timestamp.time()
                        if current_time < self.SESSION_START_TIME or current_time > self.SESSION_END_TIME:
                            continue  # Outside trading session for new entries
                        
                        # Check retest
                        retest_passed, retest_msg = self.check_retest_entry(
                            row, prev_row, dr['high'], dr['low'], breakout_type, breakout_occurred
                        )
                        
                        if not retest_passed:
                            continue
                        
                        # Check market regime
                        regime_passed, regime_msg = self.check_market_regime(nifty_data, date, breakout_type)
                        if not regime_passed:
                            logger.info(f"      ⚠️ {timestamp.strftime('%H:%M')}: {breakout_type} REJECTED - {regime_msg}")
                            continue
                        
                        # Check execution filters
                        minute_idx = minute_data.index.get_loc(timestamp)
                        filters_passed, filter_msg = self.check_execution_filters(
                            row, minute_data, minute_idx, breakout_type, ema_200_15m
                        )
                        
                        if not filters_passed:
                            logger.info(f"      ⚠️ {timestamp.strftime('%H:%M')}: {breakout_type} REJECTED - {filter_msg}")
                            continue
                        
                        # Valid retest entry!
                        logger.info(f"    ✅ {timestamp.strftime('%H:%M')}: {breakout_type} RETEST ENTRY - {retest_msg}, {filter_msg}")
                        
                        # Calculate entry and exits
                        entry_price = row['Close']
                        atr = row['ATR']
                        
                        if breakout_type == 'LONG':
                            # SL = max(1.5x ATR, retest candle low), capped at 0.7%
                            sl_atr = entry_price - (self.ATR_MULTIPLIER_FOR_SL * atr)
                            sl_candle = row['Low']
                            stop_loss = max(sl_atr, sl_candle)
                            max_sl = entry_price * (1 - self.MAXIMUM_SL_PERCENT / 100)
                            stop_loss = max(stop_loss, max_sl)
                            
                            risk = entry_price - stop_loss
                            take_profit = entry_price + (risk * self.RISK_REWARD_RATIO)
                            breakeven_price = entry_price + risk  # 1:1 R:R
                        else:  # SHORT
                            sl_atr = entry_price + (self.ATR_MULTIPLIER_FOR_SL * atr)
                            sl_candle = row['High']
                            stop_loss = min(sl_atr, sl_candle)
                            max_sl = entry_price * (1 + self.MAXIMUM_SL_PERCENT / 100)
                            stop_loss = min(stop_loss, max_sl)
                            
                            risk = stop_loss - entry_price
                            take_profit = entry_price - (risk * self.RISK_REWARD_RATIO)
                            breakeven_price = entry_price - risk  # 1:1 R:R
                        
                        # Position sizing (1% risk)
                        risk_amount = capital * (self.RISK_PER_TRADE_PERCENT / 100)
                        quantity = int((risk_amount * 5) / risk) if risk > 0 else 0  # 5x MIS leverage
                        
                        if quantity == 0:
                            continue
                        
                        logger.info(f"    🚀 ENTRY: {symbol} {breakout_type} at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{take_profit:.2f}, BE: ₹{breakeven_price:.2f}, Qty: {quantity}")
                        
                        # Mark that trade was taken today (prevent multiple trades same symbol same day)
                        trade_taken_today = True
                        
                        # Simulate trade execution
                        trailing_sl = stop_loss
                        be_moved = False
                        
                        for future_idx in range(idx + 1, len(intraday_data)):
                            future_row = intraday_data.iloc[future_idx]
                            future_time = intraday_data.index[future_idx]
                            
                            # Check for break-even move (1:1 R:R hit)
                            if not be_moved:
                                if breakout_type == 'LONG' and future_row['High'] >= breakeven_price:
                                    trailing_sl = entry_price
                                    be_moved = True
                                    logger.info(f"      📍 {future_time.strftime('%H:%M')}: Break-even moved to ₹{trailing_sl:.2f}")
                                elif breakout_type == 'SHORT' and future_row['Low'] <= breakeven_price:
                                    trailing_sl = entry_price
                                    be_moved = True
                                    logger.info(f"      📍 {future_time.strftime('%H:%M')}: Break-even moved to ₹{trailing_sl:.2f}")
                            
                            # Check TP
                            if breakout_type == 'LONG' and future_row['High'] >= take_profit:
                                pnl = quantity * (take_profit - entry_price)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': take_profit,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'Take Profit'
                                })
                                logger.info(f"    ✅ TP Hit: {symbol} {breakout_type} at ₹{take_profit:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                            elif breakout_type == 'SHORT' and future_row['Low'] <= take_profit:
                                pnl = quantity * (entry_price - take_profit)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': take_profit,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'Take Profit'
                                })
                                logger.info(f"    ✅ TP Hit: {symbol} {breakout_type} at ₹{take_profit:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                            
                            # Check SL (trailing after BE move)
                            if breakout_type == 'LONG' and future_row['Low'] <= trailing_sl:
                                pnl = quantity * (trailing_sl - entry_price)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': trailing_sl,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'Stop Loss' if not be_moved else 'Break-Even Stop'
                                })
                                logger.info(f"    ❌ SL Hit: {symbol} {breakout_type} at ₹{trailing_sl:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                            elif breakout_type == 'SHORT' and future_row['High'] >= trailing_sl:
                                pnl = quantity * (entry_price - trailing_sl)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': trailing_sl,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'Stop Loss' if not be_moved else 'Break-Even Stop'
                                })
                                logger.info(f"    ❌ SL Hit: {symbol} {breakout_type} at ₹{trailing_sl:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                            
                            # Check SuperTrend flip
                            if breakout_type == 'LONG' and future_row['SuperTrend_Direction'] == -1:
                                exit_price = future_row['Close']
                                pnl = quantity * (exit_price - entry_price)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': exit_price,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'SuperTrend Flip'
                                })
                                logger.info(f"    🔄 ST Flip: {symbol} {breakout_type} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                            elif breakout_type == 'SHORT' and future_row['SuperTrend_Direction'] == 1:
                                exit_price = future_row['Close']
                                pnl = quantity * (entry_price - exit_price)
                                capital += pnl
                                trades.append({
                                    'symbol': symbol,
                                    'entry_time': timestamp,
                                    'exit_time': future_time,
                                    'direction': breakout_type,
                                    'entry_price': entry_price,
                                    'exit_price': exit_price,
                                    'quantity': quantity,
                                    'pnl': pnl,
                                    'exit_reason': 'SuperTrend Flip'
                                })
                                logger.info(f"    🔄 ST Flip: {symbol} {breakout_type} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
                                break
                        
                        # Note: trade_taken_today prevents multiple trades same day
                        # Reset breakout flags for next symbol (but trade_taken_today stays True for this date)
                        breakout_occurred = False
                        breakout_type = None
        
        # Calculate results
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = len([t for t in trades if t['pnl'] <= 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit = sum([t['pnl'] for t in trades if t['pnl'] > 0])
        total_loss = sum([t['pnl'] for t in trades if t['pnl'] <= 0])
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else 0
        
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST COMPLETE: Alpha-Ensemble Strategy")
        logger.info("=" * 80)
        logger.info(f"\n💰 CAPITAL:")
        logger.info(f"   Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"   Final Capital:   ₹{capital:,.2f}")
        logger.info(f"   Total Return:    ₹{capital - initial_capital:,.2f} ({((capital - initial_capital) / initial_capital * 100):.2f}%)")
        logger.info(f"\n📊 TRADE STATISTICS:")
        logger.info(f"   Total Trades:    {total_trades}")
        logger.info(f"   Winning Trades:  {winning_trades}")
        logger.info(f"   Losing Trades:   {losing_trades}")
        logger.info(f"   Win Rate:        {win_rate:.2f}%")
        logger.info(f"   Profit Factor:   {profit_factor:.2f}")
        logger.info("=" * 80)
        
        return {
            'trades': trades,
            'capital': capital,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
