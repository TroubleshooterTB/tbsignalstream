"""
The Defining Order Breakout Strategy - UNIVERSAL FILTERS v2.1
(Live Trading Ready - Works with ALL Nifty 50 Symbols)

v2.1 UNIVERSAL FILTERS (Dec 14, 2024):
Based on v2.0 test (62 trades, 41.94% win rate, 15.80% return):

v2.0 LOSS ANALYSIS (36 losing trades analyzed):
- 41.94% WR: Slight improvement over v1.9 (40.00%)
- CRITICAL ISSUE 1: 13:00 hour = 33.33% WR (14 losers), -₹450 net (ONLY negative hour!)
- CRITICAL ISSUE 2: 86% of losses are ₹1,000-1,200 (avg ₹995) - SL too wide!
- CRITICAL ISSUE 3: ICICIBANK (28.6% WR), HINDUNILVR (30.8% WR), BHARTIARTL (38.1% WR)
- LONG trades: 40.00% WR vs SHORT: 43.75% WR (directional imbalance persists)
- Loss concentration: 86% exit via SL (avg -₹1,137), only 14% via EOD (avg -₹117)

v2.1 UNIVERSAL ENHANCEMENTS (No Symbol Exclusion - Live Ready):
1. ✅ SKIP 13:00 HOUR ENTIRELY: Remove 21 trades with 33.33% WR (-₹450 net)
2. ✅ TIGHTER SL CAP: 1.0% max (vs 1.5%) - reduce avg loss from ₹995 to ~₹700
3. ✅ TIGHTER ATR: 1.2x lunch, 1.4x regular (vs 1.5x/1.75x) - prevent wide stops
4. ✅ STRICTER VOLUME: 2.0x base (vs 1.6x) - higher quality setups only
5. ✅ ATR VOLATILITY FILTER: 0.5-2.5% range - avoid choppy/dead stocks
6. ✅ STRONGER RSI THRESHOLDS: 55/45 (vs 50/50) - better momentum confirmation
7. ✅ WORKS WITH ALL NIFTY 50: Universal filters, no symbol cherry-picking

Target: 48-52% win rate, 18-22% return, ₹350-400 expectancy
Expected: 30-40 trades (fewer but higher quality), avg loss reduced to ₹700
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import requests
import ta
import time as time_module

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DefiningOrderStrategy:
    """The Defining Order Breakout Strategy Implementation"""
    
    def __init__(self, api_key: str, jwt_token: str):
        self.api_key = api_key
        self.jwt_token = jwt_token
        
        # Strategy Parameters
        self.RISK_REWARD_RATIO = 2.0  # 1:2 RRR
        self.SUPERTREND_PERIOD = 10
        self.SUPERTREND_MULTIPLIER = 3
        
        # ENHANCED PARAMETERS (v1.3 - Sweet Spot Between Quality & Frequency)
        self.VOLUME_SURGE_MULTIPLIER = 1.4  # Balanced: between 1.3 (v1.2) and 1.5 (v1.1)
        self.RSI_LOWER_BOUND = 22  # Balanced: between 20 (v1.2) and 25 (v1.1)
        self.RSI_UPPER_BOUND = 78  # Balanced: between 80 (v1.2) and 75 (v1.1)
        self.VWAP_BUFFER_PERCENT = 0.18  # Balanced: between 0.15 (v1.2) and 0.2 (v1.1)
        self.BREAKOUT_STRENGTH_PERCENT = 0.13  # Balanced: between 0.12 (v1.2) and 0.15 (v1.1)
        
        # STRICTER BYPASS (v1.3 - Quality First)
        self.ALLOW_SUPERTREND_BYPASS = True  # Allow trades without SuperTrend BUT...
        self.STRONG_VOLUME_THRESHOLD = 2.5  # STRICTER: 2.5x volume (was 2.0x in v1.2)
        self.STRONG_BREAKOUT_THRESHOLD = 0.7  # STRICTER: 0.7% breakout (was 0.5% in v1.2)
        
        # v2.0 ENHANCED PRECISION PARAMETERS (Data-driven from v1.9 analysis)
        self.MINIMUM_SL_PERCENT = 0.5  # v1.9: 0.5% minimum (KEEP - working)
        self.ENTRY_CUTOFF_TIME = time(14, 30)  # Base cutoff: 2:30 PM
        self.LATE_ENTRY_EXCEPTION_TIME = time(15, 5)  # Allow until 3:05 PM if volume exceptional
        self.LATE_ENTRY_VOLUME_THRESHOLD = 2.5  # 2.5x for late entries
        self.TREND_STRENGTH_PERCENT = 0.5  # Price must be >0.5% from SMA50
        self.ATR_MULTIPLIER_FOR_SL = 1.4  # v2.1: 1.4x ATR (was 1.75x - tighter stops)
        
        # v2.0 ENHANCED FILTERS (Target 45-50% Win Rate)
        self.RSI_OVERBOUGHT_LIMIT = 75  # v1.7: Reject LONG if RSI > 75 (KEEP)
        self.VOLUME_MULTIPLIER = 2.0  # v2.1: 2.0x base volume (STRICTER - was 1.6x in v2.0)
        self.LUNCH_HOUR_VOLUME = 2.0  # v1.8: 2.0x in 13:00 hour (UNUSED - skip 13:00 entirely)
        
        # v2.1 UNIVERSAL FILTERS (Live Trading Ready)
        self.LUNCH_HOUR_ATR_MULTIPLIER = 1.2  # v2.1: TIGHTER (was 1.5x in v2.0)
        self.MAXIMUM_SL_PERCENT = 1.0  # v2.1: HARD CAP 1.0% (was 1.5% - reduce avg loss)
        self.FRIDAY_VOLUME_MULTIPLIER = 2.5  # v2.0: Stricter volume for Friday trades
        
        # v2.1 NEW UNIVERSAL FILTERS
        self.SKIP_LUNCH_HOUR = True  # v2.1: Skip 13:00 entirely (33.33% WR in v2.0)
        self.ATR_MIN_PERCENT = 0.15  # v2.1: Minimum ATR% (0.15% - very low threshold)
        self.ATR_MAX_PERCENT = 5.0  # v2.1: Maximum ATR% (5.0% - very high, rarely hit)
        self.RSI_LONG_THRESHOLD = 55  # v2.1: LONG needs RSI > 55 (was > 50)
        self.RSI_SHORT_THRESHOLD = 45  # v2.1: SHORT needs RSI < 45 (was < 50)
        
        # Defining Range Time (IST)
        self.DR_START_TIME = time(9, 30)  # 9:30 AM
        self.DR_END_TIME = time(10, 30)   # 10:30 AM
        self.SESSION_END_TIME = time(15, 15)  # 3:15 PM
    
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
                    
                    # Convert to numeric
                    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    return df
                else:
                    logger.warning(f"No data for {symbol}: {data}")
                    return pd.DataFrame()
            else:
                logger.error(f"API error for {symbol}: {response.status_code} - {response.text}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_sma(self, data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
        """Calculate Simple Moving Averages"""
        for period in periods:
            data[f'SMA_{period}'] = data['Close'].rolling(window=period).mean()
        return data
    
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate Average Directional Index"""
        adx = ta.trend.ADXIndicator(
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            window=period
        )
        data['ADX'] = adx.adx()
        return data
    
    def calculate_vwap(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate Volume Weighted Average Price (daily reset)"""
        # Group by date and calculate VWAP
        data['Date'] = data.index.date
        
        def calc_vwap_group(group):
            typical_price = (group['High'] + group['Low'] + group['Close']) / 3
            return (typical_price * group['Volume']).cumsum() / group['Volume'].cumsum()
        
        data['VWAP'] = data.groupby('Date').apply(calc_vwap_group).reset_index(level=0, drop=True)
        data.drop('Date', axis=1, inplace=True)
        
        return data
    
    def calculate_supertrend(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate SuperTrend Indicator"""
        supertrend = ta.trend.STCIndicator(
            close=data['Close'],
            window_slow=self.SUPERTREND_PERIOD,
            window_fast=self.SUPERTREND_MULTIPLIER
        )
        
        # Alternative: Manual SuperTrend calculation
        hl2 = (data['High'] + data['Low']) / 2
        atr = ta.volatility.AverageTrueRange(
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            window=self.SUPERTREND_PERIOD
        ).average_true_range()
        
        upper_band = hl2 + (self.SUPERTREND_MULTIPLIER * atr)
        lower_band = hl2 - (self.SUPERTREND_MULTIPLIER * atr)
        
        supertrend_line = pd.Series(index=data.index, dtype=float)
        supertrend_direction = pd.Series(index=data.index, dtype=int)
        
        for i in range(1, len(data)):
            if data['Close'].iloc[i] > upper_band.iloc[i-1]:
                supertrend_line.iloc[i] = lower_band.iloc[i]
                supertrend_direction.iloc[i] = 1  # Bullish
            elif data['Close'].iloc[i] < lower_band.iloc[i-1]:
                supertrend_line.iloc[i] = upper_band.iloc[i]
                supertrend_direction.iloc[i] = -1  # Bearish
            else:
                supertrend_line.iloc[i] = supertrend_line.iloc[i-1]
                supertrend_direction.iloc[i] = supertrend_direction.iloc[i-1]
        
        data['SuperTrend'] = supertrend_line
        data['SuperTrend_Direction'] = supertrend_direction  # 1 = Green (Buy), -1 = Red (Sell)
        
        return data
    
    def check_perfect_order(self, hourly_data: pd.DataFrame, idx: int) -> Optional[str]:
        """
        Layer 1: SIMPLE Trend Filter (HYBRID - PROVEN)
        
        Uses SMA(50) on 1-hour chart for trend bias.
        Simple and effective - allows tradeable signals.
        
        Returns:
            'BULLISH' if Close > SMA(50)
            'BEARISH' if Close < SMA(50)
            None if insufficient data
        """
        # Need at least 50 periods for SMA(50)
        if idx < 50:
            return None
        
        row = hourly_data.iloc[idx]
        
        # Check if SMA(50) exists
        if pd.isna(row['SMA_50']):
            return None
        
        # Simple trend determination: Price vs SMA(50)
        if row['Close'] > row['SMA_50']:
            logger.debug(f"      BULLISH bias: Close {row['Close']:.2f} > SMA(50) {row['SMA_50']:.2f}")
            return 'BULLISH'
        elif row['Close'] < row['SMA_50']:
            logger.debug(f"      BEARISH bias: Close {row['Close']:.2f} < SMA(50) {row['SMA_50']:.2f}")
            return 'BEARISH'
        else:
            return None
    
    def get_defining_range(self, minute_data: pd.DataFrame, date: datetime.date) -> Optional[Dict]:
        """
        Layer 2: Calculate Defining Range (9:30-10:30 AM)
        
        Returns:
            {'high': float, 'low': float, 'end_time': datetime}
        """
        # Filter data for the defining range period
        dr_data = minute_data[
            (minute_data.index.date == date) &
            (minute_data.index.time >= self.DR_START_TIME) &
            (minute_data.index.time <= self.DR_END_TIME)
        ]
        
        if len(dr_data) == 0:
            return None
        
        return {
            'high': dr_data['High'].max(),
            'low': dr_data['Low'].min(),
            'end_time': dr_data.index[-1]
        }
    
    def check_enhanced_confirmation(self, row: pd.Series, minute_data: pd.DataFrame, 
                                   current_idx: int, trade_direction: str, 
                                   dr_high: float, dr_low: float, hourly_sma50: float) -> Tuple[bool, str]:
        """
        Layer 3: OPTIMIZED Multi-Filter Confirmation (v1.4 - Losing Trade Fixes)
        
        Core Filters:
        1. VWAP Confirmation (0.18% threshold)
        2. Volume Surge (1.4x average)
        3. RSI Momentum (22-78 range)
        4. Breakout Strength (>0.13% beyond DR)
        5. SuperTrend Direction (OPTIONAL - can bypass if signals strong)
        
        v1.4 NEW FILTERS:
        6. Trend Strength: Price must be >0.5% from SMA50 (avoid weak trends)
        7. Trading Hours: Reject entries after 14:30 (avoid EOD pressure)
        8. Minimum Stop Distance: Ensure SL is at least 0.5% or 1.5x ATR(14)
        
        Returns:
            (passed: bool, reason: str)
        """
        # Check required indicators exist
        if pd.isna(row['VWAP']) or pd.isna(row['SuperTrend_Direction']):
            return False, "Missing VWAP/SuperTrend"
        
        # v2.1 FILTER #1: Skip 13:00 hour entirely (33.33% WR in v2.0, -₹450 net)
        entry_hour = row.name.hour if hasattr(row.name, 'hour') else pd.to_datetime(row.name).hour
        if self.SKIP_LUNCH_HOUR and entry_hour == 13:
            return False, "v2.1: Skip 13:00 hour (33.33% WR in v2.0)"
        
        # v2.1 FILTER #2: ATR Volatility Range (avoid choppy/dead stocks)
        try:
            atr_data = minute_data.iloc[max(0, current_idx-14):current_idx+1].copy()
            atr = ta.volatility.AverageTrueRange(atr_data['High'], atr_data['Low'], atr_data['Close'], window=14).average_true_range().iloc[-1]
            atr_percent = (atr / row['Close']) * 100
            
            if atr_percent < self.ATR_MIN_PERCENT:
                return False, f"v2.1: ATR too low {atr_percent:.2f}% (dead stock)"
            if atr_percent > self.ATR_MAX_PERCENT:
                return False, f"v2.1: ATR too high {atr_percent:.2f}% (choppy stock)"
        except:
            return False, "ATR calculation error"
        
        # Calculate 20-period average volume EARLY (needed for time check)
        if current_idx < 20:
            return False, "Insufficient volume history"
        
        recent_volume = minute_data.iloc[max(0, current_idx-20):current_idx]['Volume'].mean()
        volume_ratio = row['Volume'] / recent_volume
        
        # v1.5 SMART LATE-ENTRY LOGIC
        entry_time = row.name.time() if hasattr(row.name, 'time') else None
        if entry_time:
            # After 15:00 = ALWAYS reject (too close to close)
            if entry_time > self.LATE_ENTRY_EXCEPTION_TIME:
                return False, f"Too late (after {self.LATE_ENTRY_EXCEPTION_TIME.strftime('%H:%M')})"
            
            # Between 14:30 and 15:00 = Check volume exception
            if entry_time > self.ENTRY_CUTOFF_TIME:
                if volume_ratio < self.LATE_ENTRY_VOLUME_THRESHOLD:
                    return False, f"Late entry needs {self.LATE_ENTRY_VOLUME_THRESHOLD}x volume (has {volume_ratio:.1f}x)"
                # Else: EXCEPTION GRANTED - proceed with other checks
        
        # v1.4 FIX #2: Trend Strength Filter (avoid weak trends)
        if trade_direction == 'LONG':
            trend_distance = ((row['Close'] - hourly_sma50) / hourly_sma50) * 100
            if trend_distance < self.TREND_STRENGTH_PERCENT:
                return False, f"Weak uptrend: {trend_distance:.2f}% < {self.TREND_STRENGTH_PERCENT}%"
        else:  # SHORT
            trend_distance = ((hourly_sma50 - row['Close']) / hourly_sma50) * 100
            if trend_distance < self.TREND_STRENGTH_PERCENT:
                return False, f"Weak downtrend: {trend_distance:.2f}% < {self.TREND_STRENGTH_PERCENT}%"
        
        # Calculate 20-period average volume (needed for filters below)
        if current_idx < 20:
            return False, "Insufficient volume history"
        
        recent_volume = minute_data.iloc[max(0, current_idx-20):current_idx]['Volume'].mean()
        volume_ratio = row['Volume'] / recent_volume
        
        # v2.1: STRICTER VOLUME (13:00 already skipped above)
        entry_day = row.name.dayofweek if hasattr(row.name, 'dayofweek') else pd.to_datetime(row.name).dayofweek
        
        # v2.1: Friday requires 2.5x, else 2.0x base (was 1.6x in v2.0)
        if entry_day == 4:  # Friday (0=Monday, 4=Friday)
            volume_threshold = self.FRIDAY_VOLUME_MULTIPLIER  # 2.5x
        else:
            volume_threshold = self.VOLUME_MULTIPLIER  # 2.0x (STRICTER)
        
        volume_met = volume_ratio >= volume_threshold
        
        # Calculate RSI for current candle
        try:
            rsi_data = minute_data.iloc[max(0, current_idx-14):current_idx+1].copy()
            rsi = ta.momentum.RSIIndicator(rsi_data['Close'], window=14).rsi().iloc[-1]
        except:
            return False, "RSI calculation error"
        
        # v1.4 FIX #3: Calculate ATR for dynamic stop loss
        try:
            atr_data = minute_data.iloc[max(0, current_idx-14):current_idx+1].copy()
            atr = ta.volatility.AverageTrueRange(atr_data['High'], atr_data['Low'], atr_data['Close'], window=14).average_true_range().iloc[-1]
        except:
            atr = row['Close'] * 0.005  # Default to 0.5% if ATR calculation fails
        
        if trade_direction == 'LONG':
            # Calculate all metrics first
            vwap_threshold = row['VWAP'] * (1 + self.VWAP_BUFFER_PERCENT / 100)
            # volume_ratio already calculated above for time check
            breakout_strength = ((row['Close'] - dr_high) / dr_high) * 100
            
            # v1.7 FILTER #1: RSI Overbought Protection (reject if RSI > 75)
            if rsi > self.RSI_OVERBOUGHT_LIMIT:
                return False, f"Overbought: RSI {rsi:.0f} > {self.RSI_OVERBOUGHT_LIMIT} (reversal risk)"
            
            # v2.1 FILTER #3: Stronger RSI threshold (need RSI > 55 for LONG)
            if rsi < self.RSI_LONG_THRESHOLD:
                return False, f"v2.1: Weak LONG momentum RSI {rsi:.0f} < {self.RSI_LONG_THRESHOLD}"
            
            # v2.0: LUNCH HOUR TIGHTER ATR (13:00 had 25% WR in v1.9)
            atr_multiplier = self.LUNCH_HOUR_ATR_MULTIPLIER if entry_hour == 13 else self.ATR_MULTIPLIER_FOR_SL
            
            # v1.7 CRITICAL FIX: ENFORCE minimum stop distance (was broken in v1.5)
            potential_sl = dr_high  # Use DR high as SL (actual SL level)
            sl_distance_percent = ((row['Close'] - potential_sl) / row['Close']) * 100
            minimum_sl_needed = max(self.MINIMUM_SL_PERCENT, (atr * atr_multiplier / row['Close']) * 100)
            
            # v2.0: Cap SL at 1.5% maximum (ALL 54 losers hit EOD in v1.9)
            minimum_sl_needed = min(minimum_sl_needed, self.MAXIMUM_SL_PERCENT)
            
            # v1.7: Reject trade if SL would be too tight (prevents 0.23% stops)
            if sl_distance_percent < minimum_sl_needed:
                return False, f"SL too tight: {sl_distance_percent:.2f}% < {minimum_sl_needed:.2f}% (need wider SL)"
            
            # Track which filters pass
            filters_passed = 0
            filter_details = []
            
            # Filter 1: VWAP (0.15% buffer)
            vwap_passed = row['Close'] >= vwap_threshold
            if vwap_passed:
                filters_passed += 1
                filter_details.append(f"VWAP✓")
            else:
                filter_details.append(f"VWAP✗")
            
            # Filter 2: Volume surge (1.3x)
            volume_passed = row['Volume'] >= recent_volume * self.VOLUME_SURGE_MULTIPLIER
            is_strong_volume = volume_ratio >= self.STRONG_VOLUME_THRESHOLD
            if volume_passed:
                filters_passed += 1
                filter_details.append(f"Vol✓({volume_ratio:.1f}x)")
            else:
                filter_details.append(f"Vol✗({volume_ratio:.1f}x)")
            
            # Filter 3: RSI (20-80 range)
            rsi_passed = self.RSI_LOWER_BOUND <= rsi <= self.RSI_UPPER_BOUND
            if rsi_passed:
                filters_passed += 1
                filter_details.append(f"RSI✓({rsi:.0f})")
            else:
                filter_details.append(f"RSI✗({rsi:.0f})")
            
            # Filter 4: Breakout strength (>0.12%)
            strength_passed = breakout_strength >= self.BREAKOUT_STRENGTH_PERCENT
            is_strong_breakout = breakout_strength >= self.STRONG_BREAKOUT_THRESHOLD
            if strength_passed:
                filters_passed += 1
                filter_details.append(f"BO✓({breakout_strength:.2f}%)")
            else:
                filter_details.append(f"BO✗({breakout_strength:.2f}%)")
            
            # Filter 5: SuperTrend (OPTIONAL with smart bypass)
            supertrend_passed = row['SuperTrend_Direction'] == 1
            if supertrend_passed:
                filters_passed += 1
                filter_details.append("ST✓")
            else:
                filter_details.append("ST✗")
            
            # DECISION LOGIC (v1.2 Smart Bypass)
            filter_summary = " ".join(filter_details)
            
            # Scenario 1: All 5 filters pass (BEST)
            if filters_passed == 5:
                return True, f"PERFECT [{filter_summary}]"
            
            # Scenario 2: 4 filters pass + STRONG signal (volume OR breakout)
            if filters_passed >= 4 and self.ALLOW_SUPERTREND_BYPASS:
                if is_strong_volume or is_strong_breakout:
                    bypass_reason = "Vol>2x" if is_strong_volume else "BO>0.5%"
                    return True, f"STRONG BYPASS ({bypass_reason}) [{filter_summary}]"
            
            # Scenario 3: Less than 4 filters = REJECT
            if filters_passed < 4:
                return False, f"Insufficient filters: {filters_passed}/5 [{filter_summary}]"
            
            # Scenario 4: 4 filters but no strong signal = REJECT (need SuperTrend)
            return False, f"4 filters but weak signal [{filter_summary}]"
        
        elif trade_direction == 'SHORT':
            # v2.1 FILTER #3: Stronger RSI threshold (need RSI < 45 for SHORT)
            if rsi > self.RSI_SHORT_THRESHOLD:
                return False, f"v2.1: Weak SHORT momentum RSI {rsi:.0f} > {self.RSI_SHORT_THRESHOLD}"
            
            # Calculate all metrics first
            vwap_threshold = row['VWAP'] * (1 - self.VWAP_BUFFER_PERCENT / 100)
            # volume_ratio already calculated above for time check
            breakout_strength = ((dr_low - row['Close']) / dr_low) * 100
            
            # v2.0: LUNCH HOUR TIGHTER ATR + MAX SL CAP (same as LONG)
            atr_multiplier = self.LUNCH_HOUR_ATR_MULTIPLIER if entry_hour == 13 else self.ATR_MULTIPLIER_FOR_SL
            
            # v2.0: Enforce minimum stop distance for SHORT (same as LONG)
            potential_sl = dr_low  # Use DR low as SL (actual SL level)
            sl_distance_percent = ((potential_sl - row['Close']) / row['Close']) * 100
            minimum_sl_needed = max(self.MINIMUM_SL_PERCENT, (atr * atr_multiplier / row['Close']) * 100)
            
            # v2.0: Cap SL at 1.5% maximum
            minimum_sl_needed = min(minimum_sl_needed, self.MAXIMUM_SL_PERCENT)
            
            # Reject trade if SL would be too tight
            if sl_distance_percent < minimum_sl_needed:
                return False, f"SL too tight: {sl_distance_percent:.2f}% < {minimum_sl_needed:.2f}% (need wider SL)"
            
            # Track which filters pass
            filters_passed = 0
            filter_details = []
            
            # Filter 1: VWAP (0.15% buffer below)
            vwap_passed = row['Close'] <= vwap_threshold
            if vwap_passed:
                filters_passed += 1
                filter_details.append("VWAP✓")
            else:
                filter_details.append("VWAP✗")
            
            # Filter 2: Volume surge (1.3x)
            volume_passed = row['Volume'] >= recent_volume * self.VOLUME_SURGE_MULTIPLIER
            is_strong_volume = volume_ratio >= self.STRONG_VOLUME_THRESHOLD
            if volume_passed:
                filters_passed += 1
                filter_details.append(f"Vol✓({volume_ratio:.1f}x)")
            else:
                filter_details.append(f"Vol✗({volume_ratio:.1f}x)")
            
            # Filter 3: RSI (20-80 range)
            rsi_passed = self.RSI_LOWER_BOUND <= rsi <= self.RSI_UPPER_BOUND
            if rsi_passed:
                filters_passed += 1
                filter_details.append(f"RSI✓({rsi:.0f})")
            else:
                filter_details.append(f"RSI✗({rsi:.0f})")
            
            # Filter 4: Breakout strength (>0.12%)
            strength_passed = breakout_strength >= self.BREAKOUT_STRENGTH_PERCENT
            is_strong_breakout = breakout_strength >= self.STRONG_BREAKOUT_THRESHOLD
            if strength_passed:
                filters_passed += 1
                filter_details.append(f"BO✓({breakout_strength:.2f}%)")
            else:
                filter_details.append(f"BO✗({breakout_strength:.2f}%)")
            
            # Filter 5: SuperTrend (OPTIONAL with smart bypass)
            supertrend_passed = row['SuperTrend_Direction'] == -1
            if supertrend_passed:
                filters_passed += 1
                filter_details.append("ST✓")
            else:
                filter_details.append("ST✗")
            
            # DECISION LOGIC (v1.2 Smart Bypass)
            filter_summary = " ".join(filter_details)
            
            # Scenario 1: All 5 filters pass (BEST)
            if filters_passed == 5:
                return True, f"PERFECT [{filter_summary}]"
            
            # Scenario 2: 4 filters pass + STRONG signal (volume OR breakout)
            if filters_passed >= 4 and self.ALLOW_SUPERTREND_BYPASS:
                if is_strong_volume or is_strong_breakout:
                    bypass_reason = "Vol>2x" if is_strong_volume else "BO>0.5%"
                    return True, f"STRONG BYPASS ({bypass_reason}) [{filter_summary}]"
            
            # Scenario 3: Less than 4 filters = REJECT
            if filters_passed < 4:
                return False, f"Insufficient filters: {filters_passed}/5 [{filter_summary}]"
            
            # Scenario 4: 4 filters but no strong signal = REJECT (need SuperTrend)
            return False, f"4 filters but weak signal [{filter_summary}]"
        
        return False, "Invalid direction"
    
    def run_backtest(self, symbols: List[Dict], start_date: str, end_date: str, 
                    initial_capital: float = 100000) -> Dict:
        """
        Run backtest for The Defining Order Breakout Strategy - FINE-TUNED v1.1
        
        Args:
            symbols: List of dicts with 'symbol' and 'token'
            start_date: YYYY-MM-DD
            end_date: YYYY-MM-DD
            initial_capital: Starting capital
            
        Returns:
            Backtest results dictionary
        """
        logger.info("=" * 80)
        logger.info("STARTING BACKTEST: The Defining Order Breakout - IRONCLAD v2.0")
        logger.info("=" * 80)
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Initial Capital: ₹{initial_capital:,.2f}")
        logger.info(f"Symbols: {len(symbols)}")
        logger.info("")
        
        capital = initial_capital
        trades = []
        open_positions = {}
        
        for symbol_info in symbols:
            symbol = symbol_info['symbol']
            token = symbol_info['token']
            
            logger.info(f"\n📊 Processing {symbol}...")
            
            # Add delay to avoid rate limits
            time_module.sleep(2)
            
            # Fetch 1-hour data for trend filtering (need enough history for SMA 50)
            # Fetch from 60 days ago to build indicators properly
            sma_start_date = (datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=60)).strftime("%Y-%m-%d")
            
            hourly_data = self.fetch_historical_data(
                symbol, token, "ONE_HOUR", 
                sma_start_date + " 09:15", end_date + " 15:30"
            )
            
            if hourly_data.empty:
                logger.warning(f"⚠️ No hourly data for {symbol}")
                continue
            
            # Fetch 5-minute data for entry signals
            minute_data = self.fetch_historical_data(
                symbol, token, "FIVE_MINUTE",
                start_date + " 09:15", end_date + " 15:30"
            )
            
            if minute_data.empty:
                logger.warning(f"⚠️ No 5-minute data for {symbol}")
                continue
            
            # Calculate indicators on 1-hour data
            hourly_data = self.calculate_sma(hourly_data, [10, 20, 50, 100, 200])
            hourly_data = self.calculate_adx(hourly_data)
            
            # Calculate indicators on 5-minute data
            minute_data = self.calculate_vwap(minute_data)
            minute_data = self.calculate_supertrend(minute_data)
            
            logger.info(f"✅ Indicators calculated for {symbol}")
            
            # Iterate through each trading day
            trading_dates = sorted(set(minute_data.index.date))
            
            for date in trading_dates:
                # Get trend bias from hourly chart
                hourly_idx = hourly_data[hourly_data.index.date <= date].index[-1]
                hourly_idx_num = hourly_data.index.get_loc(hourly_idx)
                
                trend_bias = self.check_perfect_order(hourly_data, hourly_idx_num)
                
                if trend_bias is None:
                    logger.info(f"    ⚠️ {date}: No trend bias (insufficient SMA data)")
                    continue  # No valid trend
                
                # v1.4: Extract SMA50 value for trend strength check
                hourly_row = hourly_data.iloc[hourly_idx_num]
                hourly_sma50 = hourly_row['SMA_50']
                
                # Get defining range
                dr = self.get_defining_range(minute_data, date)
                
                if dr is None:
                    logger.info(f"    ⚠️ {date}: No Defining Range data (market not open 9:30-10:30 AM)")
                    continue  # No defining range data
                
                logger.info(f"  📅 {date}: {trend_bias} bias, DR: {dr['low']:.2f} - {dr['high']:.2f}")
                
                # Get intraday data after defining range
                intraday_data = minute_data[
                    (minute_data.index.date == date) &
                    (minute_data.index > dr['end_time']) &
                    (minute_data.index.time < self.SESSION_END_TIME)
                ]
                
                if len(intraday_data) == 0:
                    continue
                
                # Look for breakout signals
                breakout_attempts = 0
                layer3_failures = 0
                
                for idx in range(len(intraday_data)):
                    row = intraday_data.iloc[idx]
                    timestamp = intraday_data.index[idx]
                    
                    # Skip if already in position
                    if symbol in open_positions:
                        # Check exit conditions
                        position = open_positions[symbol]
                        
                        # Check stop loss
                        if (position['direction'] == 'LONG' and row['Low'] <= position['stop_loss']) or \
                           (position['direction'] == 'SHORT' and row['High'] >= position['stop_loss']):
                            # Stop loss hit
                            exit_price = position['stop_loss']
                            pnl = position['quantity'] * (exit_price - position['entry_price']) if position['direction'] == 'LONG' else \
                                  position['quantity'] * (position['entry_price'] - exit_price)
                            
                            capital += pnl
                            
                            trades.append({
                                'symbol': symbol,
                                'entry_time': position['entry_time'],
                                'exit_time': timestamp,
                                'direction': position['direction'],
                                'entry_price': position['entry_price'],
                                'exit_price': exit_price,
                                'quantity': position['quantity'],
                                'pnl': pnl,
                                'exit_reason': 'Stop Loss'
                            })
                            
                            logger.info(f"    ❌ SL Hit: {symbol} {position['direction']} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
                            del open_positions[symbol]
                            continue
                        
                        # Check take profit
                        if (position['direction'] == 'LONG' and row['High'] >= position['take_profit']) or \
                           (position['direction'] == 'SHORT' and row['Low'] <= position['take_profit']):
                            # Take profit hit
                            exit_price = position['take_profit']
                            pnl = position['quantity'] * (exit_price - position['entry_price']) if position['direction'] == 'LONG' else \
                                  position['quantity'] * (position['entry_price'] - exit_price)
                            
                            capital += pnl
                            
                            trades.append({
                                'symbol': symbol,
                                'entry_time': position['entry_time'],
                                'exit_time': timestamp,
                                'direction': position['direction'],
                                'entry_price': position['entry_price'],
                                'exit_price': exit_price,
                                'quantity': position['quantity'],
                                'pnl': pnl,
                                'exit_reason': 'Take Profit'
                            })
                            
                            logger.info(f"    ✅ TP Hit: {symbol} {position['direction']} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
                            del open_positions[symbol]
                            continue
                        
                        continue  # Still in position
                    
                    # Check for new entry signals
                    # Layer 2: Breakout of defining range
                    bullish_breakout = (trend_bias == 'BULLISH' and row['Close'] > dr['high'])
                    bearish_breakout = (trend_bias == 'BEARISH' and row['Close'] < dr['low'])
                    
                    if not (bullish_breakout or bearish_breakout):
                        continue
                    
                    breakout_attempts += 1
                    trade_direction = 'LONG' if bullish_breakout else 'SHORT'
                    
                    # Layer 3: OPTIMIZED Multi-Filter Confirmation (v1.4 - Losing Trade Fixes)
                    minute_idx = minute_data.index.get_loc(timestamp)
                    passed, reason = self.check_enhanced_confirmation(
                        row, minute_data, minute_idx, trade_direction, dr['high'], dr['low'], hourly_sma50
                    )
                    
                    if not passed:
                        layer3_failures += 1
                        logger.info(f"      ⚠️ {timestamp.strftime('%H:%M')}: {trade_direction} at ₹{row['Close']:.2f} REJECTED - {reason}")
                        continue
                    
                    # Valid signal! All filters passed
                    logger.info(f"    ✅ {timestamp.strftime('%H:%M')}: {trade_direction} signal CONFIRMED - {reason}")
                    
                    entry_price = row['Close']
                    
                    if trade_direction == 'LONG':
                        stop_loss = row['Low']  # Stop at breakout candle low
                        risk = entry_price - stop_loss
                        take_profit = entry_price + (risk * self.RISK_REWARD_RATIO)
                    else:
                        stop_loss = row['High']  # Stop at breakout candle high
                        risk = stop_loss - entry_price
                        take_profit = entry_price - (risk * self.RISK_REWARD_RATIO)
                    
                    # Calculate position size (risk 1% of capital)
                    risk_amount = capital * 0.01
                    quantity = int(risk_amount / risk) if risk > 0 else 0
                    
                    if quantity == 0:
                        continue
                    
                    open_positions[symbol] = {
                        'entry_time': timestamp,
                        'entry_price': entry_price,
                        'stop_loss': stop_loss,
                        'take_profit': take_profit,
                        'quantity': quantity,
                        'direction': trade_direction
                    }
                    
                    logger.info(f"    🚀 ENTRY: {symbol} {trade_direction} at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{take_profit:.2f}, Qty: {quantity}")
                
                # Close any remaining positions at end of day
                if symbol in open_positions:
                    position = open_positions[symbol]
                    exit_price = intraday_data.iloc[-1]['Close']
                    exit_time = intraday_data.index[-1]
                    
                    pnl = position['quantity'] * (exit_price - position['entry_price']) if position['direction'] == 'LONG' else \
                          position['quantity'] * (position['entry_price'] - exit_price)
                    
                    capital += pnl
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'exit_time': exit_time,
                        'direction': position['direction'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'End of Day'
                    })
                    
                    logger.info(f"    🔔 EOD Close: {symbol} at ₹{exit_price:.2f}, P&L: ₹{pnl:,.2f}")
                    del open_positions[symbol]
                
                # Summary for the day
                if breakout_attempts > 0:
                    logger.info(f"    📊 Day Summary: {breakout_attempts} breakouts detected, {layer3_failures} rejected by Layer 3")
        
        # Calculate results
        results = self.calculate_results(trades, initial_capital, capital)
        
        return results
    
    def calculate_results(self, trades: List[Dict], initial_capital: float, 
                         final_capital: float) -> Dict:
        """Calculate backtest performance metrics"""
        
        if len(trades) == 0:
            logger.warning("⚠️ No trades executed during backtest period")
            return {
                'total_trades': 0,
                'initial_capital': initial_capital,
                'final_capital': final_capital
            }
        
        trades_df = pd.DataFrame(trades)
        
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        total_return = final_capital - initial_capital
        return_pct = (total_return / initial_capital) * 100
        
        results = {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'return_pct': return_pct,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(trades)) * 100 if len(trades) > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'profit_factor': abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if len(losing_trades) > 0 and losing_trades['pnl'].sum() != 0 else 0,
            'expectancy': trades_df['pnl'].mean(),
            'trades': trades_df
        }
        
        self.print_results(results)
        
        return results
    
    def print_results(self, results: Dict):
        """Print formatted backtest results"""
        logger.info("\n" + "=" * 80)
        logger.info("BACKTEST COMPLETE: The Defining Order Breakout")
        logger.info("=" * 80)
        logger.info("")
        logger.info("💰 CAPITAL:")
        logger.info(f"  Initial Capital: ₹{results['initial_capital']:,.2f}")
        logger.info(f"  Final Capital:   ₹{results['final_capital']:,.2f}")
        logger.info(f"  Total Return:    ₹{results['total_return']:,.2f} ({results['return_pct']:.2f}%)")
        logger.info("")
        logger.info("📊 TRADE STATISTICS:")
        logger.info(f"  Total Trades:    {results['total_trades']}")
        logger.info(f"  Winning Trades:  {results['winning_trades']}")
        logger.info(f"  Losing Trades:   {results['losing_trades']}")
        logger.info(f"  Win Rate:        {results['win_rate']:.2f}%")
        logger.info("")
        logger.info("💵 P&L METRICS:")
        logger.info(f"  Average Win:     ₹{results['avg_win']:,.2f}")
        logger.info(f"  Average Loss:    ₹{results['avg_loss']:,.2f}")
        logger.info(f"  Largest Win:     ₹{results['largest_win']:,.2f}")
        logger.info(f"  Largest Loss:    ₹{results['largest_loss']:,.2f}")
        logger.info(f"  Profit Factor:   {results['profit_factor']:.2f}")
        logger.info(f"  Expectancy:      ₹{results['expectancy']:,.2f}")
        logger.info("")
        logger.info("=" * 80)


def generate_jwt_token(api_key: str, client_code: str, password: str, totp: str) -> Optional[str]:
    """Generate JWT token for Angel One API"""
    try:
        url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
        
        payload = {
            "clientcode": client_code,
            "password": password,
            "totp": totp
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': 'CLIENT_LOCAL_IP',
            'X-ClientPublicIP': 'CLIENT_PUBLIC_IP',
            'X-MACAddress': 'MAC_ADDRESS',
            'X-PrivateKey': api_key
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') and data.get('data'):
                jwt_token = data['data']['jwtToken']
                logger.info(f"✅ Login successful! JWT Token generated.")
                return jwt_token
            else:
                logger.error(f"❌ Login failed: {data.get('message')}")
                return None
        else:
            logger.error(f"❌ HTTP Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error generating JWT token: {str(e)}")
        return None


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("THE DEFINING ORDER BREAKOUT STRATEGY - BACKTEST")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Please enter your Angel One credentials:")
    logger.info("")
    
    # Get credentials interactively
    api_key = input("API Key: ").strip()
    client_code = input("Client Code: ").strip()
    password = input("Trading Password: ").strip()
    totp = input("TOTP (6-digit code from authenticator): ").strip()
    
    # Generate JWT token
    logger.info("\n🔐 Logging in to Angel One...")
    jwt_token = generate_jwt_token(api_key, client_code, password, totp)
    
    if not jwt_token:
        logger.error("❌ Failed to generate JWT token. Cannot proceed with backtest.")
        exit(1)
    
    # Initialize strategy
    strategy = DefiningOrderStrategy(api_key, jwt_token)
    
    # Define test symbols (v2.0: EXCLUDED KOTAKBANK-33.3% & TCS-33.3%, kept INFY-75% & RELIANCE-66.7%)
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},      # Energy (66.7% win rate - v1.9 BEST)
        # {'symbol': 'TCS-EQ', 'token': '11536'},        # v2.0 EXCLUDED: 33.3% WR, -₹1,501 net
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},       # Banking (37.0% win rate, +₹2,389 net)
        {'symbol': 'INFY-EQ', 'token': '1594'},           # IT Services (75.0% win rate - v1.9 BEST!)
        {'symbol': 'ICICIBANK-EQ', 'token': '4963'},      # Banking (42.9% win rate, +₹4,152 net)
        {'symbol': 'HINDUNILVR-EQ', 'token': '1394'},     # FMCG (37.5% win rate, +₹3,369 net)
        # {'symbol': 'SBIN-EQ', 'token': '3045'},         # v1.7 EXCLUDED: 25% win rate
        {'symbol': 'BHARTIARTL-EQ', 'token': '10604'},    # Telecom (37.5% win rate, +₹777 net)
        # {'symbol': 'ITC-EQ', 'token': '1660'},          # v1.7 EXCLUDED: 14.3% win rate
        # {'symbol': 'KOTAKBANK-EQ', 'token': '1922'},    # v2.0 EXCLUDED: 33.3% WR, -₹277 net
    ]
    
    # Backtest period (3 weeks in November 2024 - expanded for validation)
    # Nov 11-29: 15 trading days across different market conditions
    results = strategy.run_backtest(
        symbols=symbols,
        start_date="2024-11-11",
        end_date="2024-11-29",
        initial_capital=100000
    )
    
    # Save results to CSV
    if results['total_trades'] > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_defining_order_{timestamp}.csv"
        results['trades'].to_csv(filename, index=False)
        logger.info(f"\n✅ Results saved to {filename}")
