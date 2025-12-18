"""
Mean Reversion Strategy v1.0 - VWAP + RSI + Bollinger Bands
============================================================

Strategy Logic:
- Buy oversold conditions near lower Bollinger Band
- Sell overbought conditions near upper Bollinger Band
- Use VWAP as mean/target
- Higher win rate (50-60% expected) vs breakout strategies

Author: Generated December 18, 2025
Status: PAPER TRADING ONLY - Needs 1 month validation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import ta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MeanReversionStrategy:
    """Mean Reversion Strategy using VWAP, RSI, and Bollinger Bands"""
    
    def __init__(self, api_key: str, jwt_token: str):
        self.api_key = api_key
        self.jwt_token = jwt_token
        
        # Strategy Parameters - Optimized for Indian Market
        self.RSI_OVERSOLD = 30  # Buy zone
        self.RSI_OVERBOUGHT = 70  # Sell zone
        self.VOLUME_MULTIPLIER = 1.5  # Require 1.5x average volume
        self.VWAP_DEVIATION_PERCENT = 0.5  # 0.5% away from VWAP
        self.BB_PERIOD = 20  # Bollinger Band period
        self.BB_STD = 2.0  # Bollinger Band standard deviations
        self.STOP_LOSS_PERCENT = 0.3  # Tight stop loss
        self.TARGET_RR_RATIO = 1.5  # 1:1.5 risk-reward
        
        # Time filters
        self.TRADING_START = "09:30"
        self.TRADING_END = "15:00"
        self.AVOID_LUNCH_START = "12:00"
        self.AVOID_LUNCH_END = "14:00"
        
        # Position sizing
        self.POSITION_SIZE_PERCENT = 10  # 10% of capital per trade
        self.MAX_DAILY_LOSS_PERCENT = 3  # Stop trading at -3%
        self.MAX_POSITIONS = 2  # Max concurrent positions
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all required indicators"""
        
        # VWAP
        df['VWAP'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'], window=self.BB_PERIOD, window_dev=self.BB_STD)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()
        df['BB_Middle'] = bb.bollinger_mavg()
        
        # Volume moving average
        df['Volume_MA'] = df['volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['volume'] / df['Volume_MA']
        
        # Price deviation from VWAP
        df['VWAP_Deviation_Pct'] = ((df['close'] - df['VWAP']) / df['VWAP']) * 100
        
        # Candle color
        df['Candle_Color'] = np.where(df['close'] > df['open'], 'GREEN', 'RED')
        
        return df
    
    def check_long_entry(self, df: pd.DataFrame, idx: int) -> Tuple[bool, str, Dict]:
        """
        Check for LONG (BUY) entry conditions
        
        Logic:
        1. Price below VWAP by 0.5% (oversold vs mean)
        2. RSI < 30 (oversold)
        3. Price near/touching lower Bollinger Band
        4. Volume > 1.5x average (confirmation)
        5. Previous candle was RED (selling pressure exhausted)
        6. Not during lunch hour
        """
        current = df.iloc[idx]
        prev = df.iloc[idx - 1] if idx > 0 else current
        
        filters = {
            'VWAP': False,
            'RSI': False,
            'BB': False,
            'Volume': False,
            'Candle': False
        }
        
        # Time filter
        current_time = current['timestamp'].strftime('%H:%M')
        if self.AVOID_LUNCH_START <= current_time < self.AVOID_LUNCH_END:
            return False, "Lunch hour - avoid", filters
        
        # 1. VWAP Filter: Price below VWAP
        if current['VWAP_Deviation_Pct'] < -self.VWAP_DEVIATION_PERCENT:
            filters['VWAP'] = True
        
        # 2. RSI Filter: Oversold
        if current['RSI'] < self.RSI_OVERSOLD:
            filters['RSI'] = True
        
        # 3. Bollinger Band Filter: Near lower band
        bb_distance = ((current['close'] - current['BB_Lower']) / current['BB_Lower']) * 100
        if bb_distance < 0.2:  # Within 0.2% of lower band
            filters['BB'] = True
        
        # 4. Volume Filter
        if current['Volume_Ratio'] >= self.VOLUME_MULTIPLIER:
            filters['Volume'] = True
        
        # 5. Candle Color: Previous RED
        if prev['Candle_Color'] == 'RED':
            filters['Candle'] = True
        
        # Count passed filters
        passed = sum(filters.values())
        
        if passed >= 4:  # Need at least 4 out of 5 filters
            reason = f"LONG ENTRY: {passed}/5 filters [VWAP{'✓' if filters['VWAP'] else '✗'} RSI{'✓' if filters['RSI'] else '✗'}({current['RSI']:.0f}) BB{'✓' if filters['BB'] else '✗'} Vol{'✓' if filters['Volume'] else '✗'}({current['Volume_Ratio']:.1f}x) Candle{'✓' if filters['Candle'] else '✗'}]"
            return True, reason, filters
        else:
            reason = f"Insufficient filters: {passed}/5 [VWAP{'✓' if filters['VWAP'] else '✗'} RSI{'✓' if filters['RSI'] else '✗'}({current['RSI']:.0f}) BB{'✓' if filters['BB'] else '✗'} Vol{'✓' if filters['Volume'] else '✗'}({current['Volume_Ratio']:.1f}x) Candle{'✓' if filters['Candle'] else '✗'}]"
            return False, reason, filters
    
    def check_short_entry(self, df: pd.DataFrame, idx: int) -> Tuple[bool, str, Dict]:
        """
        Check for SHORT (SELL) entry conditions
        
        Logic:
        1. Price above VWAP by 0.5% (overbought vs mean)
        2. RSI > 70 (overbought)
        3. Price near/touching upper Bollinger Band
        4. Volume > 1.5x average (confirmation)
        5. Previous candle was GREEN (buying pressure exhausted)
        6. Not during lunch hour
        """
        current = df.iloc[idx]
        prev = df.iloc[idx - 1] if idx > 0 else current
        
        filters = {
            'VWAP': False,
            'RSI': False,
            'BB': False,
            'Volume': False,
            'Candle': False
        }
        
        # Time filter
        current_time = current['timestamp'].strftime('%H:%M')
        if self.AVOID_LUNCH_START <= current_time < self.AVOID_LUNCH_END:
            return False, "Lunch hour - avoid", filters
        
        # 1. VWAP Filter: Price above VWAP
        if current['VWAP_Deviation_Pct'] > self.VWAP_DEVIATION_PERCENT:
            filters['VWAP'] = True
        
        # 2. RSI Filter: Overbought
        if current['RSI'] > self.RSI_OVERBOUGHT:
            filters['RSI'] = True
        
        # 3. Bollinger Band Filter: Near upper band
        bb_distance = ((current['BB_Upper'] - current['close']) / current['BB_Upper']) * 100
        if bb_distance < 0.2:  # Within 0.2% of upper band
            filters['BB'] = True
        
        # 4. Volume Filter
        if current['Volume_Ratio'] >= self.VOLUME_MULTIPLIER:
            filters['Volume'] = True
        
        # 5. Candle Color: Previous GREEN
        if prev['Candle_Color'] == 'GREEN':
            filters['Candle'] = True
        
        # Count passed filters
        passed = sum(filters.values())
        
        if passed >= 4:  # Need at least 4 out of 5 filters
            reason = f"SHORT ENTRY: {passed}/5 filters [VWAP{'✓' if filters['VWAP'] else '✗'} RSI{'✓' if filters['RSI'] else '✗'}({current['RSI']:.0f}) BB{'✓' if filters['BB'] else '✗'} Vol{'✓' if filters['Volume'] else '✗'}({current['Volume_Ratio']:.1f}x) Candle{'✓' if filters['Candle'] else '✗'}]"
            return True, reason, filters
        else:
            reason = f"Insufficient filters: {passed}/5 [VWAP{'✓' if filters['VWAP'] else '✗'} RSI{'✓' if filters['RSI'] else '✗'}({current['RSI']:.0f}) BB{'✓' if filters['BB'] else '✗'} Vol{'✓' if filters['Volume'] else '✗'}({current['Volume_Ratio']:.1f}x) Candle{'✓' if filters['Candle'] else '✗'}]"
            return False, reason, filters
    
    def calculate_position_size(self, capital: float, entry_price: float, stop_loss: float) -> int:
        """Calculate position size based on risk management"""
        risk_per_trade = capital * (self.POSITION_SIZE_PERCENT / 100)
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk == 0:
            return 0
        
        quantity = int(risk_per_trade / price_risk)
        return max(1, quantity)  # Minimum 1 share
    
    def simulate_trade(self, entry_price: float, stop_loss: float, target: float, 
                       df: pd.DataFrame, entry_idx: int, direction: str) -> Dict:
        """Simulate a trade and return result"""
        
        for i in range(entry_idx + 1, len(df)):
            current = df.iloc[i]
            
            if direction == 'LONG':
                # Check stop loss
                if current['low'] <= stop_loss:
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'SL Hit',
                        'exit_idx': i,
                        'pnl_pct': ((stop_loss - entry_price) / entry_price) * 100
                    }
                # Check target
                if current['high'] >= target:
                    return {
                        'exit_price': target,
                        'exit_reason': 'Target Hit',
                        'exit_idx': i,
                        'pnl_pct': ((target - entry_price) / entry_price) * 100
                    }
                # Check VWAP mean reversion
                if current['close'] >= current['VWAP']:
                    return {
                        'exit_price': current['close'],
                        'exit_reason': 'VWAP Reached',
                        'exit_idx': i,
                        'pnl_pct': ((current['close'] - entry_price) / entry_price) * 100
                    }
            
            else:  # SHORT
                # Check stop loss
                if current['high'] >= stop_loss:
                    return {
                        'exit_price': stop_loss,
                        'exit_reason': 'SL Hit',
                        'exit_idx': i,
                        'pnl_pct': ((entry_price - stop_loss) / entry_price) * 100
                    }
                # Check target
                if current['low'] <= target:
                    return {
                        'exit_price': target,
                        'exit_reason': 'Target Hit',
                        'exit_idx': i,
                        'pnl_pct': ((entry_price - target) / entry_price) * 100
                    }
                # Check VWAP mean reversion
                if current['close'] <= current['VWAP']:
                    return {
                        'exit_price': current['close'],
                        'exit_reason': 'VWAP Reached',
                        'exit_idx': i,
                        'pnl_pct': ((entry_price - current['close']) / entry_price) * 100
                    }
        
        # EOD Close
        last = df.iloc[-1]
        if direction == 'LONG':
            pnl_pct = ((last['close'] - entry_price) / entry_price) * 100
        else:
            pnl_pct = ((entry_price - last['close']) / entry_price) * 100
        
        return {
            'exit_price': last['close'],
            'exit_reason': 'EOD Close',
            'exit_idx': len(df) - 1,
            'pnl_pct': pnl_pct
        }
    
    def run_backtest(self, symbol: str, df: pd.DataFrame, initial_capital: float = 100000) -> Dict:
        """Run backtest on historical data"""
        
        logging.info(f"\n{'='*80}")
        logging.info(f"BACKTESTING: {symbol} - Mean Reversion Strategy")
        logging.info(f"{'='*80}")
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        trades = []
        capital = initial_capital
        daily_loss = 0
        
        for idx in range(20, len(df)):  # Start after BB calculation period
            current = df.iloc[idx]
            current_time = current['timestamp'].strftime('%H:%M')
            
            # Check trading hours
            if current_time < self.TRADING_START or current_time >= self.TRADING_END:
                continue
            
            # Check daily loss limit
            if abs(daily_loss) >= initial_capital * (self.MAX_DAILY_LOSS_PERCENT / 100):
                logging.warning(f"⛔ Daily loss limit reached: ₹{daily_loss:.2f}")
                break
            
            # Check LONG entry
            long_signal, long_reason, long_filters = self.check_long_entry(df, idx)
            if long_signal:
                entry_price = current['close']
                stop_loss = entry_price * (1 - self.STOP_LOSS_PERCENT / 100)
                target = current['VWAP']  # Target is VWAP (mean)
                
                # If VWAP is below entry, use calculated target
                if target <= entry_price:
                    target = entry_price * (1 + (self.STOP_LOSS_PERCENT * self.TARGET_RR_RATIO) / 100)
                
                quantity = self.calculate_position_size(capital, entry_price, stop_loss)
                
                logging.info(f"  ✅ {current_time}: {long_reason}")
                logging.info(f"  🚀 ENTRY: {symbol} LONG at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{target:.2f}, Qty: {quantity}")
                
                # Simulate trade
                result = self.simulate_trade(entry_price, stop_loss, target, df, idx, 'LONG')
                pnl = quantity * (result['exit_price'] - entry_price)
                
                capital += pnl
                daily_loss += pnl
                
                exit_time = df.iloc[result['exit_idx']]['timestamp'].strftime('%H:%M')
                
                if pnl > 0:
                    logging.info(f"  ✅ {result['exit_reason']}: {symbol} LONG at ₹{result['exit_price']:.2f}, P&L: ₹{pnl:.2f}")
                else:
                    logging.info(f"  ❌ {result['exit_reason']}: {symbol} LONG at ₹{result['exit_price']:.2f}, P&L: ₹{pnl:.2f}")
                
                trades.append({
                    'symbol': symbol,
                    'direction': 'LONG',
                    'entry_time': current['timestamp'],
                    'entry_price': entry_price,
                    'exit_time': df.iloc[result['exit_idx']]['timestamp'],
                    'exit_price': result['exit_price'],
                    'exit_reason': result['exit_reason'],
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_pct': result['pnl_pct'],
                    'capital_after': capital
                })
            
            # Check SHORT entry
            short_signal, short_reason, short_filters = self.check_short_entry(df, idx)
            if short_signal:
                entry_price = current['close']
                stop_loss = entry_price * (1 + self.STOP_LOSS_PERCENT / 100)
                target = current['VWAP']  # Target is VWAP (mean)
                
                # If VWAP is above entry, use calculated target
                if target >= entry_price:
                    target = entry_price * (1 - (self.STOP_LOSS_PERCENT * self.TARGET_RR_RATIO) / 100)
                
                quantity = self.calculate_position_size(capital, entry_price, stop_loss)
                
                logging.info(f"  ✅ {current_time}: {short_reason}")
                logging.info(f"  🚀 ENTRY: {symbol} SHORT at ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}, TP: ₹{target:.2f}, Qty: {quantity}")
                
                # Simulate trade
                result = self.simulate_trade(entry_price, stop_loss, target, df, idx, 'SHORT')
                pnl = quantity * (entry_price - result['exit_price'])
                
                capital += pnl
                daily_loss += pnl
                
                exit_time = df.iloc[result['exit_idx']]['timestamp'].strftime('%H:%M')
                
                if pnl > 0:
                    logging.info(f"  ✅ {result['exit_reason']}: {symbol} SHORT at ₹{result['exit_price']:.2f}, P&L: ₹{pnl:.2f}")
                else:
                    logging.info(f"  ❌ {result['exit_reason']}: {symbol} SHORT at ₹{result['exit_price']:.2f}, P&L: ₹{pnl:.2f}")
                
                trades.append({
                    'symbol': symbol,
                    'direction': 'SHORT',
                    'entry_time': current['timestamp'],
                    'entry_price': entry_price,
                    'exit_time': df.iloc[result['exit_idx']]['timestamp'],
                    'exit_price': result['exit_price'],
                    'exit_reason': result['exit_reason'],
                    'quantity': quantity,
                    'pnl': pnl,
                    'pnl_pct': result['pnl_pct'],
                    'capital_after': capital
                })
        
        # Calculate statistics
        if len(trades) == 0:
            logging.warning(f"⚠️ No trades taken for {symbol}")
            return {
                'symbol': symbol,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'final_capital': initial_capital
            }
        
        trades_df = pd.DataFrame(trades)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        results = {
            'symbol': symbol,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(trades)) * 100,
            'total_pnl': trades_df['pnl'].sum(),
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'final_capital': capital,
            'return_pct': ((capital - initial_capital) / initial_capital) * 100,
            'trades': trades
        }
        
        logging.info(f"\n{'='*80}")
        logging.info(f"BACKTEST RESULTS: {symbol}")
        logging.info(f"{'='*80}")
        logging.info(f"Total Trades: {results['total_trades']}")
        logging.info(f"Win Rate: {results['win_rate']:.2f}%")
        logging.info(f"Total P&L: ₹{results['total_pnl']:.2f}")
        logging.info(f"Return: {results['return_pct']:.2f}%")
        logging.info(f"{'='*80}\n")
        
        return results


if __name__ == "__main__":
    # This is a template - needs actual market data to run
    logging.info("Mean Reversion Strategy v1.0")
    logging.info("Status: PAPER TRADING ONLY - Needs validation")
    logging.info("\nKey Features:")
    logging.info("- Buy oversold (RSI < 30, near lower BB, below VWAP)")
    logging.info("- Sell overbought (RSI > 70, near upper BB, above VWAP)")
    logging.info("- Target: Return to VWAP (mean reversion)")
    logging.info("- Tight SL: 0.3% (1:1.5 R/R)")
    logging.info("- Avoid lunch hour (12-2 PM)")
    logging.info("\nExpected Performance:")
    logging.info("- Win rate: 50-60% (higher than breakout)")
    logging.info("- Trades per day: 2-5 (quality over quantity)")
    logging.info("- Best in: Ranging/choppy markets")
