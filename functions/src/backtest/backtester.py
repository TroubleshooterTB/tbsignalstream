"""
Backtesting Framework
Test trading strategies on historical data with simulated execution
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestTrade:
    """Individual trade in backtest"""
    entry_time: datetime
    exit_time: datetime
    ticker: str
    entry_price: float
    exit_price: float
    quantity: int
    direction: str  # 'long' or 'short'
    pnl: float
    pnl_pct: float
    exit_reason: str
    

@dataclass
class BacktestMetrics:
    """Performance metrics from backtest"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    avg_trade_duration: float
    expectancy: float
    

class Backtester:
    """
    Backtesting engine for strategy validation on historical data.
    """
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_pct: float = 0.001,
        slippage_pct: float = 0.001
    ):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting portfolio value
            commission_pct: Commission as percentage (0.1% = 0.001)
            slippage_pct: Slippage as percentage
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
        self.trades: List[BacktestTrade] = []
        self.open_positions: Dict = {}
        self.equity_curve: List[float] = [initial_capital]
        self.daily_returns: List[float] = []
        
    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        strategy_params: Dict = None
    ) -> BacktestMetrics:
        """
        Run backtest on historical data.
        
        Args:
            data: Historical OHLCV data
            strategy_func: Strategy function that generates signals
            strategy_params: Parameters for strategy
            
        Returns:
            Backtest metrics
        """
        logger.info("Starting backtest...")
        
        strategy_params = strategy_params or {}
        
        # Iterate through historical data
        for i in range(len(data)):
            current_bar = data.iloc[i]
            historical_data = data.iloc[:i+1]
            
            # Get signal from strategy
            signal = strategy_func(historical_data, **strategy_params)
            
            if signal:
                self._process_signal(signal, current_bar)
            
            # Check stops and targets for open positions
            self._check_exits(current_bar)
            
            # Update equity curve
            current_equity = self._calculate_equity(current_bar)
            self.equity_curve.append(current_equity)
        
        # Close any remaining positions
        self._close_all_positions(data.iloc[-1])
        
        # Calculate metrics
        metrics = self._calculate_metrics()
        
        logger.info(f"Backtest complete. Total trades: {metrics.total_trades}")
        return metrics
    
    def _process_signal(self, signal: Dict, current_bar: pd.Series):
        """Process a trading signal"""
        signal_type = signal.get('type')  # 'buy' or 'sell'
        ticker = signal.get('ticker')
        quantity = signal.get('quantity', 1)
        stop_loss = signal.get('stop_loss')
        target = signal.get('target')
        
        if signal_type == 'buy' and ticker not in self.open_positions:
            # Enter long position
            entry_price = current_bar['close'] * (1 + self.slippage_pct)
            commission = entry_price * quantity * self.commission_pct
            
            cost = (entry_price * quantity) + commission
            
            if cost <= self.current_capital:
                self.open_positions[ticker] = {
                    'entry_time': current_bar.name,
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'stop_loss': stop_loss,
                    'target': target,
                    'direction': 'long'
                }
                self.current_capital -= cost
                logger.debug(f"Opened long position: {ticker} @ {entry_price}")
        
        elif signal_type == 'sell' and ticker in self.open_positions:
            # Close position
            self._close_position(ticker, current_bar, 'signal')
    
    def _check_exits(self, current_bar: pd.Series):
        """Check if any positions hit stop loss or target"""
        positions_to_close = []
        
        for ticker, position in self.open_positions.items():
            current_price = current_bar.get('close', 0)
            
            if position['direction'] == 'long':
                # Check stop loss
                if position['stop_loss'] and current_price <= position['stop_loss']:
                    positions_to_close.append((ticker, 'stop_loss'))
                # Check target
                elif position['target'] and current_price >= position['target']:
                    positions_to_close.append((ticker, 'target'))
        
        # Close positions
        for ticker, reason in positions_to_close:
            self._close_position(ticker, current_bar, reason)
    
    def _close_position(
        self,
        ticker: str,
        current_bar: pd.Series,
        exit_reason: str
    ):
        """Close an open position"""
        if ticker not in self.open_positions:
            return
        
        position = self.open_positions[ticker]
        
        exit_price = current_bar['close'] * (1 - self.slippage_pct)
        commission = exit_price * position['quantity'] * self.commission_pct
        
        proceeds = (exit_price * position['quantity']) - commission
        self.current_capital += proceeds
        
        # Calculate P&L
        pnl = proceeds - (position['entry_price'] * position['quantity'])
        pnl_pct = (pnl / (position['entry_price'] * position['quantity'])) * 100
        
        # Record trade
        trade = BacktestTrade(
            entry_time=position['entry_time'],
            exit_time=current_bar.name,
            ticker=ticker,
            entry_price=position['entry_price'],
            exit_price=exit_price,
            quantity=position['quantity'],
            direction=position['direction'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=exit_reason
        )
        self.trades.append(trade)
        
        del self.open_positions[ticker]
        logger.debug(f"Closed position: {ticker} P&L: {pnl:.2f} ({pnl_pct:.2f}%)")
    
    def _close_all_positions(self, final_bar: pd.Series):
        """Close all open positions at end of backtest"""
        for ticker in list(self.open_positions.keys()):
            self._close_position(ticker, final_bar, 'end_of_data')
    
    def _calculate_equity(self, current_bar: pd.Series) -> float:
        """Calculate current equity including open positions"""
        equity = self.current_capital
        
        for ticker, position in self.open_positions.items():
            current_price = current_bar.get('close', position['entry_price'])
            position_value = current_price * position['quantity']
            equity += position_value
        
        return equity
    
    def _calculate_metrics(self) -> BacktestMetrics:
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return BacktestMetrics(
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, total_pnl=0, total_pnl_pct=0,
                avg_win=0, avg_loss=0, largest_win=0, largest_loss=0,
                profit_factor=0, sharpe_ratio=0, max_drawdown=0,
                max_drawdown_duration=0, avg_trade_duration=0, expectancy=0
            )
        
        # Basic metrics
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.pnl for t in self.trades)
        total_pnl_pct = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t.pnl) for t in losing_trades]) if losing_trades else 0
        
        largest_win = max([t.pnl for t in self.trades])
        largest_loss = min([t.pnl for t in self.trades])
        
        # Profit factor
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Sharpe ratio
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        equity_series = pd.Series(self.equity_curve)
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = abs(drawdown.min()) * 100
        
        # Drawdown duration
        is_dd = drawdown < 0
        dd_duration = 0
        current_duration = 0
        for dd in is_dd:
            if dd:
                current_duration += 1
                dd_duration = max(dd_duration, current_duration)
            else:
                current_duration = 0
        
        # Average trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in self.trades]
        avg_duration = np.mean(durations) if durations else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=win_rate,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl_pct,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            max_drawdown_duration=dd_duration,
            avg_trade_duration=avg_duration,
            expectancy=expectancy
        )
    
    def get_equity_curve(self) -> pd.Series:
        """Get equity curve as pandas Series"""
        return pd.Series(self.equity_curve)
    
    def get_trade_log(self) -> pd.DataFrame:
        """Get trade log as DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        
        return pd.DataFrame([
            {
                'entry_time': t.entry_time,
                'exit_time': t.exit_time,
                'ticker': t.ticker,
                'direction': t.direction,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'quantity': t.quantity,
                'pnl': t.pnl,
                'pnl_pct': t.pnl_pct,
                'exit_reason': t.exit_reason
            }
            for t in self.trades
        ])
