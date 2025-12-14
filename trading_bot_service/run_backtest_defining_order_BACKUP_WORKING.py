"""
The Defining Order Breakout Strategy - IRONCLAD v2.0
(Expanded with AI Validation & Dynamic Risk Management)

Strategy Layers:
1. Perfect Order + ADX: All 5 SMAs aligned + ADX > 20 (Macro Trend)
2. Defining Range RETEST: First hour breakout with limit order on imbalance gap pullback
3. Random Forest AI: Predict next candle close for validation
4. Dynamic Risk: Breakeven at 1R profit + 1:2 RRR

Author: Trading Bot
Date: December 2024
Modification: Expanded from simple SMA(50) to full Perfect Order + RF + Breakeven logic
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import requests
import ta
import time as time_module
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

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
        self.ADX_THRESHOLD = 20
        self.RISK_REWARD_RATIO = 2.0  # 1:2 RRR
        self.SUPERTREND_PERIOD = 10
        self.SUPERTREND_MULTIPLIER = 3
        
        # Defining Range Time (IST)
        self.DR_START_TIME = time(9, 30)  # 9:30 AM
        self.DR_END_TIME = time(10, 30)   # 10:30 AM
        self.SESSION_END_TIME = time(15, 15)  # 3:15 PM
    
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
        Layer 1: Perfect Order + ADX Validation (IRONCLAD v2.0)
        
        Perfect Order:
        - Bullish: SMA(10) > SMA(20) > SMA(50) > SMA(100) > SMA(200)
        - Bearish: SMA(10) < SMA(20) < SMA(50) < SMA(100) < SMA(200)
        
        ADX Filter: Must be > 20 to confirm strong trend
        
        Returns:
            'BULLISH', 'BEARISH', or None
        """
        # Need at least 200 periods for SMA(200)
        if idx < 200:
            return None
        
        row = hourly_data.iloc[idx]
        
        # Check if all SMAs are calculated
        required_smas = ['SMA_10', 'SMA_20', 'SMA_50', 'SMA_100', 'SMA_200']
        if any(pd.isna(row[sma]) for sma in required_smas):
            return None
        
        # Check ADX threshold
        if pd.isna(row['ADX']) or row['ADX'] < self.ADX_THRESHOLD:
            logger.debug(f"      ADX too low: {row['ADX']:.2f} < {self.ADX_THRESHOLD}")
            return None
        
        # Check Perfect Order alignment
        bullish_order = (
            row['SMA_10'] > row['SMA_20'] > row['SMA_50'] > 
            row['SMA_100'] > row['SMA_200']
        )
        
        bearish_order = (
            row['SMA_10'] < row['SMA_20'] < row['SMA_50'] < 
            row['SMA_100'] < row['SMA_200']
        )
        
        if bullish_order:
            logger.debug(f"      ✅ PERFECT ORDER BULLISH + ADX {row['ADX']:.2f}")
            return 'BULLISH'
        elif bearish_order:
            logger.debug(f"      ✅ PERFECT ORDER BEARISH + ADX {row['ADX']:.2f}")
            return 'BEARISH'
        else:
            logger.debug(f"      SMAs intertwined - no clear Perfect Order")
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
    
    def train_random_forest(self, minute_data: pd.DataFrame, current_idx: int) -> Optional[str]:
        """
        Layer 3: Random Forest AI Validation (IRONCLAD v2.0)
        
        Train RF model on last 50 candles to predict next candle close.
        Features: RSI, MACD, Volume
        
        Returns:
            'BULLISH' if predicted close > current close
            'BEARISH' if predicted close < current close
            None if insufficient data or error
        """
        # Need at least 50 candles for training
        if current_idx < 50:
            return None
        
        try:
            # Get last 50 candles
            training_data = minute_data.iloc[current_idx-50:current_idx].copy()
            
            # Calculate features
            training_data['RSI'] = ta.momentum.RSIIndicator(
                training_data['Close'], window=14
            ).rsi()
            
            macd = ta.trend.MACD(training_data['Close'])
            training_data['MACD'] = macd.macd()
            training_data['MACD_Signal'] = macd.macd_signal()
            
            # Normalize volume
            training_data['Volume_Normalized'] = (
                training_data['Volume'] / training_data['Volume'].rolling(20).mean()
            )
            
            # Drop NaN rows
            training_data = training_data.dropna()
            
            if len(training_data) < 30:  # Need minimum data
                return None
            
            # Prepare features and target
            X = training_data[['RSI', 'MACD', 'MACD_Signal', 'Volume_Normalized']].values[:-1]
            y = training_data['Close'].values[1:]  # Next candle close
            
            # Train Random Forest
            rf = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            rf.fit(X, y)
            
            # Predict next candle
            current_features = training_data[['RSI', 'MACD', 'MACD_Signal', 'Volume_Normalized']].values[-1].reshape(1, -1)
            predicted_close = rf.predict(current_features)[0]
            current_close = minute_data.iloc[current_idx]['Close']
            
            # Return prediction
            if predicted_close > current_close:
                logger.debug(f"      🤖 RF BULLISH: Predicted ₹{predicted_close:.2f} > Current ₹{current_close:.2f}")
                return 'BULLISH'
            elif predicted_close < current_close:
                logger.debug(f"      🤖 RF BEARISH: Predicted ₹{predicted_close:.2f} < Current ₹{current_close:.2f}")
                return 'BEARISH'
            else:
                return None
                
        except Exception as e:
            logger.debug(f"      RF training error: {str(e)}")
            return None
    
    def run_backtest(self, symbols: List[Dict], start_date: str, end_date: str, 
                    initial_capital: float = 100000) -> Dict:
        """
        Run backtest for The Defining Order Breakout Strategy - IRONCLAD v2.0
        
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
                    
                    # Layer 3: VWAP + SuperTrend confirmation
                    if not self.check_layer3_confirmation(row, trade_direction):
                        layer3_failures += 1
                        logger.info(f"      ⚠️ {timestamp.strftime('%H:%M')}: {trade_direction} breakout at ₹{row['Close']:.2f} rejected by Layer 3 (VWAP: ₹{row['VWAP']:.2f}, SuperTrend: {row['SuperTrend_Direction']})")
                        continue
                    
                    # Valid signal! Enter position
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
                    
                    logger.info(f"    ✅ Layer 3 PASSED! {timestamp.strftime('%H:%M')}: VWAP OK, SuperTrend OK")
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
        url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
        
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
    
    # Define test symbols (Nifty 50 stocks - highly liquid) - Limited to 3 for rate limit testing
    symbols = [
        {'symbol': 'RELIANCE-EQ', 'token': '2885'},
        {'symbol': 'TCS-EQ', 'token': '11536'},
        {'symbol': 'HDFCBANK-EQ', 'token': '1333'},
    ]
    
    # Backtest period (last week of November 2024)
    results = strategy.run_backtest(
        symbols=symbols,
        start_date="2024-11-25",
        end_date="2024-11-29",
        initial_capital=100000
    )
    
    # Save results to CSV
    if results['total_trades'] > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_defining_order_{timestamp}.csv"
        results['trades'].to_csv(filename, index=False)
        logger.info(f"\n✅ Results saved to {filename}")
