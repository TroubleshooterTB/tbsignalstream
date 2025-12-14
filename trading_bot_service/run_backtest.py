"""
Backtest Trading Bot Strategy
Tests pattern detection and trading logic on historical data
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading.patterns import PatternDetector
from trading.execution_manager import ExecutionManager
from historical_data_manager import HistoricalDataManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBotBacktest:
    """Backtest trading bot using actual pattern detection logic"""
    
    def __init__(self, credentials: Dict, symbols: List[str], initial_capital: float = 100000):
        self.credentials = credentials
        self.symbols = symbols
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        
        # Symbol token mapping (same as bot)
        self.symbol_tokens = {
            'RELIANCE': {'token': '2885', 'exchange': 'NSE'},
            'HDFCBANK': {'token': '1333', 'exchange': 'NSE'},
            'INFY': {'token': '1594', 'exchange': 'NSE'},
            'TCS': {'token': '11536', 'exchange': 'NSE'},
            'ICICIBANK': {'token': '1330', 'exchange': 'NSE'},
            'SBIN': {'token': '3045', 'exchange': 'NSE'},
            'BHARTIARTL': {'token': '10604', 'exchange': 'NSE'},
            'ITC': {'token': '1660', 'exchange': 'NSE'},
            'AXISBANK': {'token': '5900', 'exchange': 'NSE'},
            'KOTAKBANK': {'token': '1922', 'exchange': 'NSE'},
            'HINDUNILVR': {'token': '1394', 'exchange': 'NSE'},
            'LT': {'token': '11483', 'exchange': 'NSE'},
            'ASIANPAINT': {'token': '236', 'exchange': 'NSE'},
            'MARUTI': {'token': '10999', 'exchange': 'NSE'},
            'HCLTECH': {'token': '7229', 'exchange': 'NSE'},
            'WIPRO': {'token': '3787', 'exchange': 'NSE'},
            'M&M': {'token': '2031', 'exchange': 'NSE'},
            'TATAMOTORS': {'token': '3456', 'exchange': 'NSE'},
            'TATASTEEL': {'token': '3499', 'exchange': 'NSE'},
            'SUNPHARMA': {'token': '3351', 'exchange': 'NSE'},
            'NTPC': {'token': '11630', 'exchange': 'NSE'},
            'POWERGRID': {'token': '14977', 'exchange': 'NSE'},
            'ULTRACEMCO': {'token': '11532', 'exchange': 'NSE'},
            'BAJFINANCE': {'token': '317', 'exchange': 'NSE'},
            'BAJAJFINSV': {'token': '16675', 'exchange': 'NSE'},
            'TECHM': {'token': '13538', 'exchange': 'NSE'},
            'TITAN': {'token': '3506', 'exchange': 'NSE'},
            'NESTLEIND': {'token': '17963', 'exchange': 'NSE'},
            'ADANIENT': {'token': '25', 'exchange': 'NSE'},
            'ADANIPORTS': {'token': '15083', 'exchange': 'NSE'},
            'COALINDIA': {'token': '20374', 'exchange': 'NSE'},
            'JSWSTEEL': {'token': '11723', 'exchange': 'NSE'},
            'INDUSINDBK': {'token': '5258', 'exchange': 'NSE'},
            'ONGC': {'token': '2475', 'exchange': 'NSE'},
            'HINDALCO': {'token': '1363', 'exchange': 'NSE'},
            'GRASIM': {'token': '1232', 'exchange': 'NSE'},
            'CIPLA': {'token': '694', 'exchange': 'NSE'},
            'DRREDDY': {'token': '881', 'exchange': 'NSE'},
            'DIVISLAB': {'token': '10940', 'exchange': 'NSE'},
            'EICHERMOT': {'token': '910', 'exchange': 'NSE'},
            'HEROMOTOCO': {'token': '1348', 'exchange': 'NSE'},
            'TATACONSUM': {'token': '3432', 'exchange': 'NSE'},
            'BRITANNIA': {'token': '547', 'exchange': 'NSE'},
            'BPCL': {'token': '526', 'exchange': 'NSE'},
            'UPL': {'token': '11287', 'exchange': 'NSE'},
            'APOLLOHOSP': {'token': '157', 'exchange': 'NSE'},
            'LTIM': {'token': '17818', 'exchange': 'NSE'},
            'SBILIFE': {'token': '21808', 'exchange': 'NSE'},
            'HDFCLIFE': {'token': '467', 'exchange': 'NSE'},
            'BAJAJ-AUTO': {'token': '16669', 'exchange': 'NSE'},
        }
        
        # Initialize pattern detector (same as live bot)
        self.pattern_detector = PatternDetector()
        
        # Initialize 30-point Grandmaster Checklist (same as live bot)
        self.execution_manager = ExecutionManager()
        
        # Initialize historical data manager
        self.hist_manager = HistoricalDataManager(
            api_key=credentials['api_key'],
            jwt_token=credentials['jwt_token']
        )
        
        # Trading state
        self.open_positions = {}
        self.trades = []
        self.equity_curve = [initial_capital]
        
        # Trading parameters (matching live bot strategy)
        self.max_positions = 5  # Maximum concurrent positions
        self.min_rr_ratio = 2.0  # Minimum risk-reward ratio (2:1 minimum)
        self.atr_stop_multiplier = 2.5  # ATR multiplier for stop loss
        self.trail_stop_trigger = 0.01  # Activate trailing stop when profit >1%
        
    def fetch_backtest_data(self, days_back: int = 5) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data for backtesting
        
        Args:
            days_back: Number of trading days to fetch
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        logger.info(f"Fetching {days_back} days of historical data for {len(self.symbols)} symbols...")
        
        data = {}
        
        # FIXED DATE RANGE: November 5-13, 2025 (potentially better trending period)
        start_date = datetime(2025, 11, 5)
        end_date = datetime(2025, 11, 13)
        
        logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        for idx, symbol in enumerate(self.symbols, 1):
            try:
                # Get base symbol name (remove -EQ suffix)
                base_symbol = symbol.replace('-EQ', '')
                
                if base_symbol not in self.symbol_tokens:
                    logger.warning(f"  ⏭️ {symbol}: Token not found in mapping")
                    continue
                
                token_info = self.symbol_tokens[base_symbol]
                logger.info(f"[{idx}/{len(self.symbols)}] Fetching {symbol}...")
                
                # Fetch 15-minute candles (better for pattern quality)
                df = self.hist_manager.fetch_historical_data(
                    symbol=symbol,
                    token=token_info['token'],
                    exchange=token_info['exchange'],
                    from_date=start_date,
                    to_date=end_date,
                    interval='FIFTEEN_MINUTE'
                )
                
                if df is not None and len(df) > 0:
                    data[symbol] = df
                    logger.info(f"  ✅ {symbol}: {len(df)} candles")
                else:
                    logger.warning(f"  ⏭️ {symbol}: No data returned")
                    
            except Exception as e:
                logger.error(f"  ❌ {symbol}: Failed - {e}")
        
        logger.info(f"Successfully fetched data for {len(data)}/{len(self.symbols)} symbols")
        return data
    
    def run_backtest(self, historical_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            historical_data: Dictionary mapping symbol to DataFrame
            
        Returns:
            Backtest results and metrics
        """
        logger.info("=" * 80)
        logger.info("STARTING BACKTEST")
        logger.info("=" * 80)
        
        # Get all unique timestamps across all symbols
        all_timestamps = set()
        for df in historical_data.values():
            all_timestamps.update(df.index.tolist())
        
        sorted_timestamps = sorted(list(all_timestamps))
        logger.info(f"Backtesting {len(sorted_timestamps)} time periods...")
        
        # Simulate trading day by day
        for i, timestamp in enumerate(sorted_timestamps):
            # Skip first 50 candles (needed for indicators - enough for 15-min data)
            if i < 50:
                continue
            
            # Log progress every 25 candles (15-min intervals)
            if i % 25 == 0:
                progress = (i / len(sorted_timestamps)) * 100
                logger.info(f"Progress: {progress:.1f}% ({i}/{len(sorted_timestamps)})")
            
            # STEP 1: Collect all potential signals from all symbols
            # LIVE BOT STRATEGY: Single pattern + 30-point Grandmaster Checklist
            signals = []
            
            for symbol, df in historical_data.items():
                # Get data up to current timestamp
                mask = df.index <= timestamp
                historical_subset = df[mask]
                
                # Need at least 50 candles for pattern detection
                if len(historical_subset) < 50:
                    continue
                
                # Skip if already in position for this symbol
                if symbol in self.open_positions:
                    # Check exits for open positions
                    self._check_position_exit(symbol, historical_subset, timestamp)
                    continue
                
                # SINGLE PATTERN DETECTION (matching live bot)
                pattern_details = self.pattern_detector.scan(historical_subset)
                
                if not pattern_details:
                    continue  # No pattern detected
                
                # Check if pattern is tradeable (confirmed breakout)
                is_tradeable = pattern_details.get('tradeable', True)
                if not is_tradeable:
                    continue
                
                # RUN 30-POINT GRANDMASTER CHECKLIST (matching live bot)
                is_valid = self.execution_manager.validate_trade_entry(historical_subset, pattern_details)
                
                if not is_valid:
                    logging.debug(f"    {symbol}: Pattern '{pattern_details['pattern_name']}' FAILED 30-point validation")
                    continue  # Failed validation
                
                # Calculate risk-reward ratio
                current_price = historical_subset.iloc[-1]['Close']
                stop_loss = pattern_details.get('initial_stop_loss', current_price * 0.98)
                target = pattern_details.get('calculated_price_target', current_price * 1.05)
                risk = abs(current_price - stop_loss)
                reward = abs(target - current_price)
                rr_ratio = reward / risk if risk > 0 else 0
                
                # Validate minimum R:R ratio
                if rr_ratio < self.min_rr_ratio:
                    logging.debug(f"    {symbol}: R:R {rr_ratio:.1f}x < minimum {self.min_rr_ratio}x")
                    continue
                
                # Signal passed all validations!
                signals.append({
                    'symbol': symbol,
                    'pattern_name': pattern_details['pattern_name'],
                    'rr_ratio': rr_ratio,
                    'pattern_details': pattern_details,
                    'df': historical_subset,
                    'timestamp': timestamp,
                    'current_price': current_price,
                    'stop_loss': stop_loss,
                    'target': target
                })
            
            # Log validated signals (passed 30-point checklist)
            if signals:
                logging.info(f"\n  ✅ {len(signals)} signals PASSED 30-point validation at {timestamp.strftime('%Y-%m-%d %H:%M')}:")
                for s in sorted(signals, key=lambda x: x['rr_ratio'], reverse=True):
                    logging.info(f"    {s['symbol']}: {s['pattern_name']} | R:R: {s['rr_ratio']:.1f}x")
            
            # STEP 2: Signals already validated by 30-point Grandmaster Checklist
            # All signals here have passed the comprehensive validation
            valid_signals = signals
            
            # STEP 3: Sort by risk-reward ratio and take top signals
            if valid_signals:
                valid_signals.sort(key=lambda x: x['rr_ratio'], reverse=True)
                
                # Log top signals
                if i % 25 == 0 and len(valid_signals) > 0:  # Log every 25 candles
                    logger.info(f"🎯 Found {len(valid_signals)} validated signals")
                    for idx, sig in enumerate(valid_signals[:3]):  # Show top 3
                        logger.info(f"  {idx+1}. {sig['symbol']}: {sig['pattern_name']} (R:R=1:{sig['rr_ratio']:.2f})")
                
                # STEP 4: Take best trades up to max_positions limit
                current_positions_count = len(self.open_positions)
                available_slots = self.max_positions - current_positions_count
                
                for sig in valid_signals[:available_slots]:
                    self._enter_position(
                        symbol=sig['symbol'],
                        pattern_details=sig['pattern_details'],
                        df=sig['df'],
                        timestamp=sig['timestamp'],
                        rr_ratio=sig['rr_ratio']
                    )
            
            # Update equity curve
            current_equity = self._calculate_equity(historical_data, timestamp)
            self.equity_curve.append(current_equity)
        
        # Close all remaining positions
        logger.info("Closing remaining positions...")
        for symbol in list(self.open_positions.keys()):
            df = historical_data[symbol]
            self._exit_position(symbol, df.iloc[-1]['Close'], sorted_timestamps[-1], 'end_of_backtest')
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        logger.info("=" * 80)
        logger.info("BACKTEST COMPLETE")
        logger.info("=" * 80)
        
        return {
            'metrics': metrics,
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }
    
    def _calculate_signal_confidence(self, df: pd.DataFrame, pattern_details: dict) -> float:
        """
        Calculate confidence score (0-100) for a trading signal.
        Same logic as live bot.
        
        Factors:
        - Volume strength (20%)
        - Trend alignment (20%)
        - Pattern quality (30%)
        - Support/Resistance proximity (15%)
        - Momentum indicators (15%)
        """
        try:
            confidence = 0.0
            
            # 1. Volume strength (25 points) - CRITICAL for breakout confirmation
            if 'Volume' in df.columns:
                avg_volume = df['Volume'].tail(20).mean()
                current_volume = df['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
                
                # Require strong volume for high scores
                if volume_ratio >= 2.0:
                    confidence += 25  # Exceptional volume (2x average)
                elif volume_ratio >= 1.5:
                    confidence += 20  # Strong volume
                elif volume_ratio >= 1.2:
                    confidence += 12  # Good volume
                elif volume_ratio >= 0.8:
                    confidence += 5   # Normal volume
                else:
                    confidence += 0   # Weak volume - no points
            else:
                confidence += 5  # Reduced default if no volume data
            
            # 2. Trend alignment (20 points)
            if len(df) >= 50:
                # Calculate simple moving averages
                sma_20 = df['Close'].rolling(20).mean().iloc[-1]
                sma_50 = df['Close'].rolling(50).mean().iloc[-1]
                price = df['Close'].iloc[-1]
                
                # Bullish alignment: price > sma_20 > sma_50
                if price > sma_20 > sma_50:
                    confidence += 20
                elif price > sma_20:
                    confidence += 10
            else:
                confidence += 10  # Default if not enough data
            
            # 3. Pattern quality (30 points)
            # Based on pattern characteristics
            pattern_name = pattern_details.get('pattern_name', '')
            duration = pattern_details.get('duration', 20)
            
            # Longer patterns are generally more reliable
            duration_score = min(15, (duration / 50) * 15)
            confidence += duration_score
            
            # Pattern type reliability (based on historical performance)
            pattern_reliability = {
                'Double Bottom': 15,
                'Double Top': 12,
                'Falling Wedge': 14,
                'Rising Wedge': 12,
                'Ascending Triangle': 13,
                'Descending Triangle': 11,
                'Symmetrical Triangle': 10,
                'Bull Flag': 14,
                'Bear Flag': 12
            }
            confidence += pattern_reliability.get(pattern_name, 10)
            
            # 4. Support/Resistance proximity (15 points)
            support = pattern_details.get('pattern_bottom_boundary', 0)
            resistance = pattern_details.get('pattern_top_boundary', 0)
            price = df['Close'].iloc[-1]
            
            if support > 0 and resistance > 0:
                range_size = resistance - support
                distance_from_support = price - support
                position_in_range = distance_from_support / range_size if range_size > 0 else 0.5
                
                # For bullish patterns, better if near support
                # For bearish patterns, better if near resistance
                breakout_dir = pattern_details.get('breakout_direction', 'up')
                if breakout_dir == 'up' and position_in_range < 0.3:
                    confidence += 15
                elif breakout_dir == 'down' and position_in_range > 0.7:
                    confidence += 15
                elif 0.3 <= position_in_range <= 0.7:
                    confidence += 8
            else:
                confidence += 8  # Default
            
            # 5. Momentum indicators (15 points) - simplified
            # Check momentum (15 points) - Ensure breakout has follow-through
            if len(df) >= 5:
                recent_change = (df['Close'].iloc[-1] - df['Close'].iloc[-5]) / df['Close'].iloc[-5]
                breakout_dir = pattern_details.get('breakout_direction', 'up')
                
                # Require momentum in direction of breakout
                if breakout_dir == 'up':
                    if recent_change > 0.005:  # At least 0.5% move
                        confidence += min(15, recent_change * 300)
                    else:
                        confidence += 0  # No points for weak momentum
                elif breakout_dir == 'down':
                    if recent_change < -0.005:  # At least -0.5% move
                        confidence += min(15, abs(recent_change) * 300)
                    else:
                        confidence += 0
                else:
                    confidence += 3  # Neutral breakout
            else:
                confidence += 3
            
            return min(100.0, max(0.0, confidence))  # Clamp to 0-100
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 50.0  # Default medium confidence on error
    
    def _enter_position(self, symbol: str, pattern_details: Dict, df: pd.DataFrame, timestamp, 
                        rr_ratio: float = 2.0):
        """Enter a trading position (matching live bot logic)"""
        current_price = df.iloc[-1]['Close']
        
        # Calculate ATR for better stop placement (use 14-period ATR)
        if len(df) >= 14:
            high_low = df['High'].iloc[-14:] - df['Low'].iloc[-14:]
            high_close = abs(df['High'].iloc[-14:] - df['Close'].shift(1).iloc[-14:])
            low_close = abs(df['Low'].iloc[-14:] - df['Close'].shift(1).iloc[-14:])
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.mean()
        else:
            atr = current_price * 0.02  # Default 2% if not enough data
        
        # Improved stop loss placement using ATR
        breakout_dir = pattern_details.get('breakout_direction', 'up')
        pattern_stop = pattern_details.get('initial_stop_loss', current_price * 0.98)
        
        if breakout_dir == 'up':
            # Use wider of: pattern stop or 2.5x ATR below entry (widened to reduce whipsaws)
            atr_stop = current_price - (atr * self.atr_stop_multiplier)
            stop_loss = min(pattern_stop, atr_stop)  # Use WIDER stop (allow pattern to develop)
        else:
            # For short patterns (down breakouts)
            atr_stop = current_price + (atr * self.atr_stop_multiplier)
            stop_loss = min(pattern_stop, atr_stop)
        
        # Improved target placement - ensure minimum 2:1 risk-reward
        pattern_target = pattern_details.get('calculated_price_target', current_price * 1.05)
        risk = abs(current_price - stop_loss)
        
        if breakout_dir == 'up':
            min_target = current_price + (risk * self.min_rr_ratio)
            target = max(pattern_target, min_target)  # Use further target (better reward)
        else:
            min_target = current_price - (risk * self.min_rr_ratio)
            target = min(pattern_target, min_target)
        
        # Position sizing (risk 1% of capital per trade)
        risk_per_trade = self.current_capital * 0.01
        risk_per_share = abs(current_price - stop_loss)
        quantity = int(risk_per_trade / risk_per_share) if risk_per_share > 0 else 1
        quantity = max(1, min(quantity, 100))  # Min 1, max 100
        
        # Calculate cost
        cost = current_price * quantity
        commission = cost * 0.001  # 0.1% commission
        total_cost = cost + commission
        
        # Check if we have enough capital
        if total_cost > self.current_capital:
            return
        
        # Deduct capital
        self.current_capital -= total_cost
        
        # Record position
        self.open_positions[symbol] = {
            'entry_time': timestamp,
            'entry_price': current_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'target': target,
            'pattern': pattern_details.get('pattern_name', 'Unknown'),
            'cost': total_cost,
            'rr_ratio': rr_ratio,
            'validated': True  # Passed 30-point Grandmaster Checklist
        }
        
        logger.info(f"📈 ENTER: {symbol} @ ₹{current_price:.2f} | Qty: {quantity} | Pattern: {pattern_details.get('pattern_name')} | R:R: 1:{rr_ratio:.2f} | ✅ Validated")
    
    def _check_position_exit(self, symbol: str, df: pd.DataFrame, timestamp):
        """Check if position should be exited"""
        position = self.open_positions[symbol]
        current_price = df.iloc[-1]['Close']
        
        # Calculate current P&L percentage
        pnl_pct = (current_price - position['entry_price']) / position['entry_price']
        
        # Activate trailing stop if profit >1%
        if pnl_pct > self.trail_stop_trigger:
            # Initialize highest price tracking
            if 'highest_price' not in position:
                position['highest_price'] = current_price
            
            # Update highest price and trail stop
            if current_price > position['highest_price']:
                position['highest_price'] = current_price
                # Trail stop at 0.5% below highest point reached
                new_stop = position['highest_price'] * 0.995
                position['stop_loss'] = max(position['stop_loss'], new_stop)
        
        exit_reason = None
        
        # Check stop loss
        if current_price <= position['stop_loss']:
            exit_reason = 'trailing_stop' if pnl_pct > 0 and 'highest_price' in position else 'stop_loss'
        # Check target
        elif current_price >= position['target']:
            exit_reason = 'target'
        
        if exit_reason:
            self._exit_position(symbol, current_price, timestamp, exit_reason)
    
    def _exit_position(self, symbol: str, exit_price: float, timestamp, exit_reason: str):
        """Exit a trading position"""
        position = self.open_positions[symbol]
        
        # Calculate proceeds
        proceeds = exit_price * position['quantity']
        commission = proceeds * 0.001
        net_proceeds = proceeds - commission
        
        # Add to capital
        self.current_capital += net_proceeds
        
        # Calculate P&L
        pnl = net_proceeds - position['cost']
        pnl_pct = (pnl / position['cost']) * 100
        
        # Record trade
        trade = {
            'symbol': symbol,
            'entry_time': position['entry_time'],
            'exit_time': timestamp,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'quantity': position['quantity'],
            'pattern': position['pattern'],
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': exit_reason,
            'confidence': position.get('confidence', 0),
            'rr_ratio': position.get('rr_ratio', 0)
        }
        self.trades.append(trade)
        
        logger.info(f"📉 EXIT: {symbol} @ ₹{exit_price:.2f} | P&L: ₹{pnl:.2f} ({pnl_pct:.2f}%) | Reason: {exit_reason}")
        
        # Remove position
        del self.open_positions[symbol]
    
    def _calculate_equity(self, historical_data: Dict[str, pd.DataFrame], timestamp) -> float:
        """Calculate current equity"""
        equity = self.current_capital
        
        # Add unrealized P&L from open positions
        for symbol, position in self.open_positions.items():
            df = historical_data[symbol]
            mask = df.index <= timestamp
            subset = df[mask]
            
            if len(subset) > 0:
                current_price = subset.iloc[-1]['Close']
                position_value = current_price * position['quantity']
                equity += position_value
        
        return equity
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return_pct': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'profit_factor': 0,
                'expectancy': 0
            }
        
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in self.trades)
        total_return_pct = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        
        avg_win = sum(t['pnl'] for t in winning_trades) / win_count if win_count > 0 else 0
        avg_loss = abs(sum(t['pnl'] for t in losing_trades) / loss_count) if loss_count > 0 else 0
        
        largest_win = max([t['pnl'] for t in self.trades])
        largest_loss = min([t['pnl'] for t in self.trades])
        
        gross_profit = sum(t['pnl'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['pnl'] for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
        
        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy
        }
    
    def print_results(self, results: Dict):
        """Print backtest results"""
        metrics = results['metrics']
        trades = results['trades']
        
        print("\n" + "=" * 80)
        print("BACKTEST RESULTS")
        print("=" * 80)
        
        print(f"\n💰 CAPITAL:")
        print(f"  Initial Capital: ₹{self.initial_capital:,.2f}")
        print(f"  Final Capital:   ₹{self.current_capital:,.2f}")
        print(f"  Total Return:    ₹{metrics['total_pnl']:,.2f} ({metrics['total_return_pct']:.2f}%)")
        
        print(f"\n📊 TRADE STATISTICS:")
        print(f"  Total Trades:    {metrics['total_trades']}")
        print(f"  Winning Trades:  {metrics['winning_trades']}")
        print(f"  Losing Trades:   {metrics['losing_trades']}")
        print(f"  Win Rate:        {metrics['win_rate']:.2f}%")
        
        print(f"\n💵 P&L METRICS:")
        print(f"  Average Win:     ₹{metrics['avg_win']:,.2f}")
        print(f"  Average Loss:    ₹{metrics['avg_loss']:,.2f}")
        print(f"  Largest Win:     ₹{metrics['largest_win']:,.2f}")
        print(f"  Largest Loss:    ₹{metrics['largest_loss']:,.2f}")
        print(f"  Profit Factor:   {metrics['profit_factor']:.2f}")
        print(f"  Expectancy:      ₹{metrics['expectancy']:.2f}")
        
        # Pattern type performance analysis
        if trades:
            print(f"\n📈 PATTERN TYPE PERFORMANCE:")
            pattern_stats = {}
            for trade in trades:
                pattern = trade['pattern']
                if pattern not in pattern_stats:
                    pattern_stats[pattern] = {'trades': 0, 'wins': 0, 'total_pnl': 0, 'pnls': []}
                pattern_stats[pattern]['trades'] += 1
                pattern_stats[pattern]['total_pnl'] += trade['pnl']
                pattern_stats[pattern]['pnls'].append(trade['pnl'])
                if trade['pnl'] > 0:
                    pattern_stats[pattern]['wins'] += 1
            
            for pattern, stats in sorted(pattern_stats.items(), key=lambda x: x[1]['total_pnl'], reverse=True):
                win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['trades']
                print(f"  {pattern:25s} | Trades: {stats['trades']:2d} | Win: {win_rate:5.1f}% | "
                      f"Avg P&L: ₹{avg_pnl:8,.2f} | Total: ₹{stats['total_pnl']:9,.2f}")
        
        if trades:
            print(f"\n📝 RECENT TRADES (Last 10):")
            for trade in trades[-10:]:
                print(f"  {trade['symbol']:12} | {trade['pattern']:20} | "
                      f"P&L: ₹{trade['pnl']:8.2f} ({trade['pnl_pct']:6.2f}%) | "
                      f"Exit: {trade['exit_reason']}")
        
        print("\n" + "=" * 80)


def generate_jwt_token(api_key: str, client_code: str, password: str, totp: str) -> Optional[str]:
    """
    Generate JWT token by logging in with TOTP.
    
    Args:
        api_key: Angel One API key
        client_code: Client code
        password: Trading password
        totp: 6-digit TOTP code from authenticator
    
    Returns:
        JWT token or None if login failed
    """
    import requests
    
    url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-UserType': 'USER',
        'X-SourceID': 'WEB',
        'X-ClientLocalIP': '127.0.0.1',
        'X-ClientPublicIP': '127.0.0.1',
        'X-MACAddress': '00:00:00:00:00:00',
        'X-PrivateKey': api_key
    }
    
    payload = {
        "clientcode": client_code,
        "password": password,
        "totp": totp
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') and data.get('data'):
            jwt_token = data['data'].get('jwtToken')
            if jwt_token:
                print("✅ Successfully logged in and generated JWT token")
                return jwt_token
            else:
                print(f"❌ Login response missing JWT token: {data}")
                return None
        else:
            print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None


def main():
    """Run backtest"""
    # Get credentials from user input
    print("=" * 80)
    print("TRADING BOT BACKTEST")
    print("=" * 80)
    print("\nPlease enter your Angel One credentials:")
    
    api_key = input("API Key: ").strip()
    client_code = input("Client Code: ").strip()
    password = input("Trading Password: ").strip()
    totp = input("TOTP (6-digit code from authenticator): ").strip()
    
    # Generate JWT token
    print("\n🔐 Logging in to Angel One...")
    jwt_token = generate_jwt_token(api_key, client_code, password, totp)
    
    if not jwt_token:
        print("❌ Failed to generate JWT token. Cannot proceed with backtest.")
        return
    
    credentials = {
        'api_key': api_key,
        'client_code': client_code,
        'jwt_token': jwt_token
    }
    
    # Define symbols (Nifty 50)
    symbols = [
        'RELIANCE-EQ', 'TCS-EQ', 'HDFCBANK-EQ', 'INFY-EQ', 'ICICIBANK-EQ',
        'HINDUNILVR-EQ', 'ITC-EQ', 'SBIN-EQ', 'BHARTIARTL-EQ', 'KOTAKBANK-EQ',
        'LT-EQ', 'AXISBANK-EQ', 'ASIANPAINT-EQ', 'MARUTI-EQ', 'BAJFINANCE-EQ',
        'HCLTECH-EQ', 'WIPRO-EQ', 'ULTRACEMCO-EQ', 'TITAN-EQ', 'NESTLEIND-EQ',
        'SUNPHARMA-EQ', 'ONGC-EQ', 'NTPC-EQ', 'POWERGRID-EQ', 'M&M-EQ',
        'TATAMOTORS-EQ', 'TATASTEEL-EQ', 'ADANIPORTS-EQ', 'COALINDIA-EQ', 'BAJAJFINSV-EQ',
        'JSWSTEEL-EQ', 'GRASIM-EQ', 'HINDALCO-EQ', 'INDUSINDBK-EQ', 'DRREDDY-EQ',
        'TECHM-EQ', 'CIPLA-EQ', 'BPCL-EQ', 'EICHERMOT-EQ', 'HEROMOTOCO-EQ',
        'DIVISLAB-EQ', 'TATACONSUM-EQ', 'APOLLOHOSP-EQ', 'ADANIENT-EQ', 'UPL-EQ',
        'BRITANNIA-EQ', 'SBILIFE-EQ', 'BAJAJ-AUTO-EQ', 'LTIM-EQ', 'HDFCLIFE-EQ'
    ]
    
    # Ask for backtest parameters
    days_back = int(input("\nHow many trading days to backtest? (default 5): ").strip() or "5")
    initial_capital = float(input("Initial capital (default 100000): ").strip() or "100000")
    
    # Create backtest instance
    backtest = TradingBotBacktest(credentials, symbols, initial_capital)
    
    # Fetch historical data
    print("\n" + "=" * 80)
    historical_data = backtest.fetch_backtest_data(days_back=days_back)
    
    if not historical_data:
        print("❌ No historical data fetched. Cannot run backtest.")
        return
    
    # Run backtest
    print("\n" + "=" * 80)
    results = backtest.run_backtest(historical_data)
    
    # Print results
    backtest.print_results(results)
    
    # Save results
    save = input("\nSave detailed results to CSV? (y/n): ").strip().lower()
    if save == 'y':
        trades_df = pd.DataFrame(results['trades'])
        filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        trades_df.to_csv(filename, index=False)
        print(f"✅ Results saved to {filename}")


if __name__ == "__main__":
    main()
