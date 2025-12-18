"""
Complete Alpha-Ensemble Backtest with Nifty 200 Dynamic Screening
==================================================================

Integrates:
1. High-frequency screener (top 25 from Nifty 200)
2. Proven retest entry logic from alpha_ensemble_strategy.py
3. 2.5:1 R:R with break-even trailing
4. Comprehensive performance metrics

Mathematical Edge: Φ (Expectancy) = (0.40 × AvgWin) - (0.60 × AvgLoss) > 0
"""

import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
import logging
from typing import List, Dict
import ta
from alpha_ensemble_screener import AlphaEnsembleScreener

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CompleteAlphaEnsembleBacktest:
    """
    Full implementation combining screening + strategy execution
    Uses proven logic from original alpha_ensemble_strategy.py
    """
    
    def __init__(self, screener: AlphaEnsembleScreener):
        self.screener = screener
        
        # Strategy parameters (from proven alpha_ensemble_strategy.py)
        self.DR_START_TIME = time(9, 30)
        self.DR_END_TIME = time(10, 30)
        self.RISK_REWARD_RATIO = 2.5
        self.ATR_MULTIPLIER_FOR_SL = 1.5
        self.MAX_SL_PERCENT = 0.7
        self.RISK_PER_TRADE_PERCENT = 1.0
        self.BREAKEVEN_RATIO = 1.0
        self.SLIPPAGE_PERCENT = 0.05
        self.RETEST_TOLERANCE = 0.1
        self.SESSION_END_TIME = time(15, 15)
        
        # Execution filters (Layer 3)
        self.ADX_MIN = 25
        self.VOLUME_MIN_MULTIPLIER = 2.5
        self.RSI_LONG_MIN = 55
        self.RSI_LONG_MAX = 65
        self.RSI_SHORT_MIN = 35
        self.RSI_SHORT_MAX = 45
        self.EMA50_DISTANCE_MAX = 2.0
        self.ATR_MIN_PERCENT = 0.10
        self.ATR_MAX_PERCENT = 5.0
        
        # MIS Leverage
        self.MIS_LEVERAGE = 5
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        # VWAP (intraday calculation)
        df['Date'] = df.index.date
        
        def calc_vwap_group(group):
            typical_price = (group['High'] + group['Low'] + group['Close']) / 3
            vwap = (typical_price * group['Volume']).cumsum() / group['Volume'].cumsum()
            return vwap
        
        vwap_values = []
        for date, group in df.groupby('Date'):
            vwap = calc_vwap_group(group)
            vwap_values.append(vwap)
        
        df['VWAP'] = pd.concat(vwap_values)
        
        # EMAs
        df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['EMA50'] = ta.trend.ema_indicator(df['Close'], window=50)
        df['EMA200'] = ta.trend.ema_indicator(df['Close'], window=200)
        
        # ADX
        adx_indicator = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
        df['ADX'] = adx_indicator.adx()
        
        # RSI
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        # ATR
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
        
        # SuperTrend
        st_indicator = ta.trend.PSARIndicator(df['High'], df['Low'], df['Close'])
        df['SuperTrend'] = st_indicator.psar()
        
        df.drop('Date', axis=1, inplace=True, errors='ignore')
        
        return df
    
    def get_defining_range(self, df: pd.DataFrame) -> Dict:
        """Calculate Defining Range (9:30 AM - 10:30 AM)"""
        dr_data = df.between_time(self.DR_START_TIME, self.DR_END_TIME)
        
        if dr_data.empty:
            return None
        
        return {
            'high': dr_data['High'].max(),
            'low': dr_data['Low'].min()
        }
    
    def check_execution_filters(self, row: pd.Series, direction: str, atr_pct: float) -> tuple:
        """
        LAYER 3: 5-Factor Execution Filters
        
        Returns: (passed: bool, reason: str)
        """
        # 1. ADX Filter (MOST CRITICAL)
        if pd.isna(row['ADX']) or row['ADX'] < self.ADX_MIN:
            return False, f"ADX too low: {row['ADX']:.1f} < {self.ADX_MIN}"
        
        # 2. Volume Filter (using volume from screening - already passed)
        # We assume screener already validated volume, so skip redundant check
        
        # 3. RSI Sweet Spot
        if direction == 'LONG':
            if row['RSI'] < self.RSI_LONG_MIN or row['RSI'] > self.RSI_LONG_MAX:
                return False, f"RSI outside sweet spot: {row['RSI']:.1f} (need {self.RSI_LONG_MIN}-{self.RSI_LONG_MAX})"
        else:  # SHORT
            if row['RSI'] < self.RSI_SHORT_MIN or row['RSI'] > self.RSI_SHORT_MAX:
                return False, f"RSI outside sweet spot: {row['RSI']:.1f} (need {self.RSI_SHORT_MIN}-{self.RSI_SHORT_MAX})"
        
        # 4. Distance from 50 EMA
        if not pd.isna(row['EMA50']):
            ema50_dist_pct = abs((row['Close'] - row['EMA50']) / row['EMA50']) * 100
            if ema50_dist_pct > self.EMA50_DISTANCE_MAX:
                return False, f"Too far from EMA50: {ema50_dist_pct:.2f}% > {self.EMA50_DISTANCE_MAX}%"
        
        # 5. ATR Window
        if atr_pct < self.ATR_MIN_PERCENT or atr_pct > self.ATR_MAX_PERCENT:
            return False, f"ATR outside window: {atr_pct:.2f}% (need {self.ATR_MIN_PERCENT}-{self.ATR_MAX_PERCENT}%)"
        
        return True, "All filters passed"
    
    def check_retest_entry(self, row: pd.Series, direction: str, dr: Dict, 
                           prev_breakout: bool) -> tuple:
        """
        LAYER 3: Retest Entry Logic (Sniper Execution)
        
        Entry Rules:
        - LONG: After breakout above DR High, enter on pullback to VWAP/EMA20
        - SHORT: After breakout below DR Low, enter on pullback to VWAP/EMA20
        - Must stay above/below DR during retest
        
        Returns: (entry_signal: bool, entry_price: float, retest_type: str)
        """
        if not prev_breakout:
            return False, 0, ""
        
        # Check proximity to VWAP
        vwap_dist_pct = abs((row['Close'] - row['VWAP']) / row['VWAP']) * 100
        
        # Check proximity to EMA20
        ema20_dist_pct = abs((row['Close'] - row['EMA20']) / row['EMA20']) * 100 if not pd.isna(row['EMA20']) else 999
        
        if direction == 'LONG':
            # Must stay above DR High during retest
            if row['Low'] < dr['high']:
                return False, 0, ""
            
            # Check VWAP touch
            if vwap_dist_pct <= self.RETEST_TOLERANCE:
                return True, row['Close'], 'VWAP'
            
            # Check EMA20 touch
            if ema20_dist_pct <= self.RETEST_TOLERANCE:
                return True, row['Close'], 'EMA20'
        
        else:  # SHORT
            # Must stay below DR Low during retest
            if row['High'] > dr['low']:
                return False, 0, ""
            
            # Check VWAP touch
            if vwap_dist_pct <= self.RETEST_TOLERANCE:
                return True, row['Close'], 'VWAP'
            
            # Check EMA20 touch
            if ema20_dist_pct <= self.RETEST_TOLERANCE:
                return True, row['Close'], 'EMA20'
        
        return False, 0, ""
    
    def calculate_position_size(self, capital: float, entry_price: float, 
                                stop_loss: float) -> int:
        """
        Calculate position size based on:
        - 1% risk per trade
        - 5x MIS leverage
        """
        risk_amount = capital * (self.RISK_PER_TRADE_PERCENT / 100)
        risk_per_share = abs(entry_price - stop_loss)
        
        if risk_per_share == 0:
            return 0
        
        base_quantity = int(risk_amount / risk_per_share)
        
        # Apply 5x MIS leverage
        leveraged_quantity = base_quantity * self.MIS_LEVERAGE
        
        return leveraged_quantity
    
    def execute_strategy_on_candidate(self, candidate: Dict, capital: float) -> List[Dict]:
        """
        Execute Alpha-Ensemble strategy on a single candidate stock
        
        Returns: List of trades generated
        """
        symbol = candidate['symbol']
        df = candidate['data_15m'].copy()
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Get ATR percentage
        atr_pct = candidate['atr_pct']
        
        # Get defining range
        dr = self.get_defining_range(df)
        
        if dr is None:
            logger.warning(f"❌ {symbol}: No defining range found")
            return []
        
        trades = []
        position = None
        breakout_detected = False
        
        # Iterate through candles after DR end time
        post_dr_data = df[df.index.time > self.DR_END_TIME]
        
        for i in range(len(post_dr_data)):
            row = post_dr_data.iloc[i]
            
            # Skip if before screening time (10:30 AM)
            if row.name.time() < self.screener.SCREENING_TIME:
                continue
            
            # Check for position exit first
            if position is not None:
                # Time-based exit
                if row.name.time() >= self.SESSION_END_TIME:
                    exit_price = row['Close']
                    pnl = (exit_price - position['entry']) * position['quantity'] if position['direction'] == 'LONG' \
                          else (position['entry'] - exit_price) * position['quantity']
                    
                    # Apply slippage
                    pnl *= (1 - self.SLIPPAGE_PERCENT / 100)
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry'],
                        'exit_time': row.name,
                        'exit_price': exit_price,
                        'direction': position['direction'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'TIME_EXIT'
                    })
                    
                    position = None
                    breakout_detected = False
                    continue
                
                # Stop loss hit
                if position['direction'] == 'LONG' and row['Low'] <= position['stop_loss']:
                    exit_price = position['stop_loss']
                    pnl = (exit_price - position['entry']) * position['quantity']
                    pnl *= (1 - self.SLIPPAGE_PERCENT / 100)
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry'],
                        'exit_time': row.name,
                        'exit_price': exit_price,
                        'direction': position['direction'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'STOP_LOSS'
                    })
                    
                    position = None
                    breakout_detected = False
                    continue
                
                elif position['direction'] == 'SHORT' and row['High'] >= position['stop_loss']:
                    exit_price = position['stop_loss']
                    pnl = (position['entry'] - exit_price) * position['quantity']
                    pnl *= (1 - self.SLIPPAGE_PERCENT / 100)
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry'],
                        'exit_time': row.name,
                        'exit_price': exit_price,
                        'direction': position['direction'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'STOP_LOSS'
                    })
                    
                    position = None
                    breakout_detected = False
                    continue
                
                # Take profit hit
                if position['direction'] == 'LONG' and row['High'] >= position['take_profit']:
                    exit_price = position['take_profit']
                    pnl = (exit_price - position['entry']) * position['quantity']
                    pnl *= (1 - self.SLIPPAGE_PERCENT / 100)
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry'],
                        'exit_time': row.name,
                        'exit_price': exit_price,
                        'direction': position['direction'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'TAKE_PROFIT'
                    })
                    
                    position = None
                    breakout_detected = False
                    continue
                
                elif position['direction'] == 'SHORT' and row['Low'] <= position['take_profit']:
                    exit_price = position['take_profit']
                    pnl = (position['entry'] - exit_price) * position['quantity']
                    pnl *= (1 - self.SLIPPAGE_PERCENT / 100)
                    
                    trades.append({
                        'symbol': symbol,
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry'],
                        'exit_time': row.name,
                        'exit_price': exit_price,
                        'direction': position['direction'],
                        'quantity': position['quantity'],
                        'pnl': pnl,
                        'exit_reason': 'TAKE_PROFIT'
                    })
                    
                    position = None
                    breakout_detected = False
                    continue
                
                # Break-even trailing (at 1:1 R:R)
                current_profit_pct = abs((row['Close'] - position['entry']) / position['entry']) * 100
                initial_risk_pct = abs((position['entry'] - position['initial_sl']) / position['entry']) * 100
                
                if current_profit_pct >= initial_risk_pct * self.BREAKEVEN_RATIO:
                    if position['stop_loss'] != position['entry']:
                        logger.info(f"   🔒 Moving SL to break-even: {position['entry']:.2f}")
                        position['stop_loss'] = position['entry']
            
            # No position - look for entry
            else:
                # Detect breakout
                if not breakout_detected:
                    # LONG breakout: Close above DR High
                    if row['Close'] > dr['high']:
                        breakout_detected = True
                        breakout_direction = 'LONG'
                        continue
                    
                    # SHORT breakout: Close below DR Low
                    elif row['Close'] < dr['low']:
                        breakout_detected = True
                        breakout_direction = 'SHORT'
                        continue
                
                # Breakout detected - wait for retest
                if breakout_detected:
                    entry_signal, entry_price, retest_type = self.check_retest_entry(
                        row, breakout_direction, dr, True
                    )
                    
                    if entry_signal:
                        # Check execution filters
                        filters_passed, filter_reason = self.check_execution_filters(
                            row, breakout_direction, atr_pct
                        )
                        
                        if not filters_passed:
                            logger.info(f"   ❌ {symbol}: Retest found but filters failed - {filter_reason}")
                            breakout_detected = False  # Reset
                            continue
                        
                        # Calculate stop loss
                        if breakout_direction == 'LONG':
                            # SL = max(1.5x ATR, retest candle low), cap at 0.7%
                            atr_based_sl = entry_price - (row['ATR'] * self.ATR_MULTIPLIER_FOR_SL)
                            candle_based_sl = row['Low']
                            stop_loss = max(atr_based_sl, candle_based_sl)
                            
                            # Cap at 0.7%
                            max_allowed_sl = entry_price * (1 - self.MAX_SL_PERCENT / 100)
                            stop_loss = max(stop_loss, max_allowed_sl)
                        
                        else:  # SHORT
                            atr_based_sl = entry_price + (row['ATR'] * self.ATR_MULTIPLIER_FOR_SL)
                            candle_based_sl = row['High']
                            stop_loss = min(atr_based_sl, candle_based_sl)
                            
                            # Cap at 0.7%
                            max_allowed_sl = entry_price * (1 + self.MAX_SL_PERCENT / 100)
                            stop_loss = min(stop_loss, max_allowed_sl)
                        
                        # Calculate take profit (2.5:1 R:R)
                        risk = abs(entry_price - stop_loss)
                        
                        if breakout_direction == 'LONG':
                            take_profit = entry_price + (risk * self.RISK_REWARD_RATIO)
                        else:
                            take_profit = entry_price - (risk * self.RISK_REWARD_RATIO)
                        
                        # Calculate position size
                        quantity = self.calculate_position_size(capital, entry_price, stop_loss)
                        
                        if quantity == 0:
                            logger.warning(f"   ⚠️ {symbol}: Position size = 0, skipping")
                            breakout_detected = False
                            continue
                        
                        # Enter position
                        position = {
                            'entry': entry_price,
                            'entry_time': row.name,
                            'stop_loss': stop_loss,
                            'initial_sl': stop_loss,
                            'take_profit': take_profit,
                            'quantity': quantity,
                            'direction': breakout_direction
                        }
                        
                        logger.info(f"\n   ✅ {symbol} {breakout_direction} ENTRY:")
                        logger.info(f"      Entry: ₹{entry_price:.2f} ({retest_type} retest)")
                        logger.info(f"      SL: ₹{stop_loss:.2f} | TP: ₹{take_profit:.2f} | R:R: 2.5:1")
                        logger.info(f"      Qty: {quantity:,} shares (5x leverage)")
                        logger.info(f"      Filters: ADX={row['ADX']:.1f}, RSI={row['RSI']:.1f}, ATR={atr_pct:.2f}%")
        
        return trades
    
    def run_multi_day_backtest(self, start_date: str, end_date: str, 
                               initial_capital: float = 100000) -> Dict:
        """
        Run backtest with daily screening and rotation
        
        For each trading day:
        1. Screen Nifty 200 at 10:30 AM
        2. Select top 25 candidates
        3. Monitor for retest entries
        4. Execute trades
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 MULTI-DAY BACKTEST WITH DYNAMIC SCREENING")
        logger.info(f"{'='*80}")
        logger.info(f"Start Date: {start_date}")
        logger.info(f"End Date: {end_date}")
        logger.info(f"Initial Capital: ₹{initial_capital:,.2f}\n")
        
        all_trades = []
        capital = initial_capital
        daily_capitals = []
        
        # Generate trading dates (simplified - would need market calendar in production)
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        current_date = start
        while current_date <= end:
            # Skip weekends (simplified)
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                date_str = current_date.strftime("%Y-%m-%d")
                
                logger.info(f"\n{'='*80}")
                logger.info(f"📅 TRADING DAY: {date_str}")
                logger.info(f"{'='*80}")
                
                # Fetch Nifty data for market alignment
                to_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
                from_date = (current_date - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
                
                nifty_data = self.screener.fetch_historical_data(
                    'NIFTY 50', '99926000', 'FIVE_MINUTE', from_date, to_date
                )
                
                if nifty_data.empty:
                    logger.warning(f"⚠️ No Nifty data for {date_str} - skipping")
                    current_date += timedelta(days=1)
                    continue
                
                # Screen for top 25 candidates
                top_25 = self.screener.screen_stocks(date_str, nifty_data)
                
                if not top_25:
                    logger.warning(f"⚠️ No candidates passed screening for {date_str}")
                    current_date += timedelta(days=1)
                    continue
                
                # Execute strategy on selected candidates
                day_trades = []
                for candidate in top_25:
                    trades = self.execute_strategy_on_candidate(candidate, capital)
                    day_trades.extend(trades)
                
                # Update capital
                for trade in day_trades:
                    capital += trade['pnl']
                    all_trades.append(trade)
                
                daily_capitals.append({
                    'date': date_str,
                    'capital': capital,
                    'trades': len(day_trades)
                })
                
                logger.info(f"\n📊 Day Summary: {len(day_trades)} trades, Capital: ₹{capital:,.2f}")
            
            current_date += timedelta(days=1)
        
        # Calculate final performance
        return self._calculate_performance(all_trades, initial_capital, capital, daily_capitals)
    
    def _calculate_performance(self, trades: List[Dict], initial_capital: float, 
                              final_capital: float, daily_capitals: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {
                'trades': [],
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'expectancy': 0,
                'max_drawdown': 0,
                'final_capital': initial_capital,
                'total_return': 0,
                'sharpe_ratio': 0
            }
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / len(trades)) * 100
        
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in losing_trades))
        
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        # Expectancy (Φ)
        avg_win = total_profit / len(winning_trades) if winning_trades else 0
        avg_loss = total_loss / len(losing_trades) if losing_trades else 0
        loss_rate = (len(losing_trades) / len(trades))
        
        expectancy = (win_rate/100 * avg_win) - (loss_rate * avg_loss)
        
        # Max drawdown
        running_capital = initial_capital
        peak_capital = initial_capital
        max_drawdown = 0
        
        for trade in trades:
            running_capital += trade['pnl']
            if running_capital > peak_capital:
                peak_capital = running_capital
            drawdown = ((peak_capital - running_capital) / peak_capital) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Sharpe ratio (simplified - assumes daily returns)
        if daily_capitals:
            daily_returns = []
            for i in range(1, len(daily_capitals)):
                ret = (daily_capitals[i]['capital'] - daily_capitals[i-1]['capital']) / daily_capitals[i-1]['capital']
                daily_returns.append(ret)
            
            if daily_returns:
                sharpe_ratio = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'trades': trades,
            'total_trades': len(trades),
            'win_rate': win_rate,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'final_capital': final_capital,
            'total_return': ((final_capital - initial_capital) / initial_capital) * 100,
            'sharpe_ratio': sharpe_ratio,
            'daily_capitals': daily_capitals
        }


def main():
    """Run complete backtest with screening"""
    print("\n" + "=" * 80)
    print("ALPHA-ENSEMBLE BACKTEST WITH DYNAMIC NIFTY 200 SCREENER")
    print("=" * 80)
    print("\nEnter your Angel One credentials:")
    
    client_code = input("Client Code: ").strip()
    password = input("Password/MPIN: ").strip()
    totp = input("TOTP Code: ").strip()
    api_key = input("API Key: ").strip()
    
    # Authenticate
    import requests
    url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
    
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
    
    payload = {
        "clientcode": client_code,
        "password": password,
        "totp": totp
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('status') and data.get('data'):
            jwt_token = data['data']['jwtToken']
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed")
            return
    else:
        print("❌ Authentication failed")
        return
    
    # Create screener and backtest instances
    screener = AlphaEnsembleScreener(api_key, jwt_token)
    backtest = CompleteAlphaEnsembleBacktest(screener)
    
    # Get backtest parameters
    print("\nBacktest Parameters:")
    start_date = input("Start Date (YYYY-MM-DD): ").strip()
    end_date = input("End Date (YYYY-MM-DD): ").strip()
    
    # Run backtest
    results = backtest.run_multi_day_backtest(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )
    
    # Print comprehensive results
    print("\n" + "=" * 80)
    print("📊 FINAL PERFORMANCE SUMMARY")
    print("=" * 80)
    
    print(f"\n💰 CAPITAL PERFORMANCE:")
    print(f"   Initial Capital:  ₹{100000:,.2f}")
    print(f"   Final Capital:    ₹{results['final_capital']:,.2f}")
    print(f"   Total Return:     {results['total_return']:.2f}%")
    print(f"   Max Drawdown:     {results['max_drawdown']:.2f}%")
    
    print(f"\n📈 TRADE STATISTICS:")
    print(f"   Total Trades:     {results['total_trades']}")
    print(f"   Winning Trades:   {results['winning_trades']}")
    print(f"   Losing Trades:    {results['losing_trades']}")
    print(f"   Win Rate:         {results['win_rate']:.2f}%")
    
    print(f"\n🎯 PERFORMANCE METRICS:")
    print(f"   Profit Factor:    {results['profit_factor']:.2f}")
    print(f"   Expectancy (Φ):   ₹{results['expectancy']:,.2f}")
    print(f"   Avg Win:          ₹{results['avg_win']:,.2f}")
    print(f"   Avg Loss:         ₹{results['avg_loss']:,.2f}")
    print(f"   Sharpe Ratio:     {results['sharpe_ratio']:.2f}")
    
    print("\n" + "=" * 80)
    print("✅ VALIDATION TARGETS:")
    print("=" * 80)
    print(f"   Win Rate > 40%?       {results['win_rate']:.2f}% {'✅ YES' if results['win_rate'] > 40 else '❌ NO'}")
    print(f"   Profit Factor > 1.0?  {results['profit_factor']:.2f} {'✅ YES' if results['profit_factor'] > 1.0 else '❌ NO'}")
    print(f"   Positive Expectancy?  ₹{results['expectancy']:,.2f} {'✅ YES' if results['expectancy'] > 0 else '❌ NO'}")
    print(f"   Positive Return?      {results['total_return']:.2f}% {'✅ YES' if results['total_return'] > 0 else '❌ NO'}")
    print("=" * 80)
    
    # Print sample trades
    if results['trades']:
        print("\n📋 SAMPLE TRADES (First 10):")
        print("=" * 80)
        for i, trade in enumerate(results['trades'][:10], 1):
            pnl_symbol = "🟢" if trade['pnl'] > 0 else "🔴"
            print(f"{i:2d}. {pnl_symbol} {trade['symbol']:<15} {trade['direction']:<5} "
                  f"Entry: ₹{trade['entry_price']:8.2f} → Exit: ₹{trade['exit_price']:8.2f} | "
                  f"P&L: ₹{trade['pnl']:10,.2f} ({trade['exit_reason']})")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
