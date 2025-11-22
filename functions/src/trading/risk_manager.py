"""
Risk Management System
Implements portfolio-level risk controls and position sizing
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    max_portfolio_heat: float = 0.06  # Max 6% portfolio at risk
    max_position_size_pct: float = 0.02  # Max 2% per position
    max_drawdown_pct: float = 0.10  # Max 10% drawdown
    max_daily_loss_pct: float = 0.03  # Max 3% daily loss
    max_correlation: float = 0.7  # Max correlation between positions
    max_open_positions: int = 5  # Max concurrent positions
    min_risk_reward: float = 2.0  # Min 1:2 risk/reward
    max_sector_exposure: float = 0.30  # Max 30% in one sector


@dataclass
class Position:
    """Position information"""
    ticker: str
    entry_price: float
    current_price: float
    quantity: int
    stop_loss: float
    sector: str
    entry_date: datetime
    
    @property
    def risk_amount(self) -> float:
        """Calculate risk amount for this position"""
        return abs(self.entry_price - self.stop_loss) * self.quantity
    
    @property
    def current_value(self) -> float:
        """Current position value"""
        return self.current_price * self.quantity
    
    @property
    def pnl(self) -> float:
        """Current P&L"""
        return (self.current_price - self.entry_price) * self.quantity


class RiskManager:
    """
    Comprehensive risk management system for trading operations.
    """
    
    def __init__(
        self,
        portfolio_value: float,
        risk_limits: Optional[RiskLimits] = None
    ):
        """
        Initialize Risk Manager.
        
        Args:
            portfolio_value: Total portfolio value
            risk_limits: Risk limit configuration
        """
        self.portfolio_value = portfolio_value
        self.limits = risk_limits or RiskLimits()
        self.positions: List[Position] = []
        self.daily_pnl = 0.0
        self.peak_portfolio_value = portfolio_value
        self.trade_history: List[Dict] = []
        
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        volatility: float = 0.02
    ) -> int:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            entry_price: Entry price for the position
            stop_loss: Stop loss price
            volatility: Stock volatility (standard deviation of returns)
            
        Returns:
            Recommended position size (number of shares)
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(entry_price - stop_loss)
            
            if risk_per_share == 0:
                logger.warning("Stop loss equals entry price. Cannot calculate position size.")
                return 0
            
            # Calculate max risk amount (2% of portfolio)
            max_risk_amount = self.portfolio_value * self.limits.max_position_size_pct
            
            # Base position size
            base_size = int(max_risk_amount / risk_per_share)
            
            # Adjust for volatility (reduce size for high volatility)
            volatility_factor = 1.0 - (volatility / 0.05)  # Normalize around 5% vol
            volatility_factor = max(0.5, min(1.5, volatility_factor))
            
            adjusted_size = int(base_size * volatility_factor)
            
            # Ensure position doesn't exceed max portfolio percentage
            max_value = self.portfolio_value * self.limits.max_position_size_pct
            max_shares = int(max_value / entry_price)
            
            final_size = min(adjusted_size, max_shares)
            
            logger.info(f"Calculated position size: {final_size} shares")
            return final_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def check_portfolio_heat(self, new_position_risk: float = 0) -> Tuple[bool, float]:
        """
        Check if total portfolio heat (risk) is within limits.
        
        Args:
            new_position_risk: Risk amount of new position to add
            
        Returns:
            (is_acceptable, current_heat_percentage)
        """
        # Calculate current portfolio heat
        total_risk = sum(pos.risk_amount for pos in self.positions)
        total_risk += new_position_risk
        
        heat_percentage = (total_risk / self.portfolio_value) * 100
        
        is_acceptable = heat_percentage <= (self.limits.max_portfolio_heat * 100)
        
        logger.info(f"Portfolio heat: {heat_percentage:.2f}% (Limit: {self.limits.max_portfolio_heat * 100}%)")
        
        return is_acceptable, heat_percentage
    
    def check_drawdown(self) -> Tuple[bool, float]:
        """
        Check current drawdown against limit.
        
        Returns:
            (is_acceptable, current_drawdown_percentage)
        """
        current_value = self.portfolio_value + sum(pos.pnl for pos in self.positions)
        drawdown = (self.peak_portfolio_value - current_value) / self.peak_portfolio_value
        
        is_acceptable = drawdown <= self.limits.max_drawdown_pct
        
        if current_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_value
            drawdown = 0
        
        logger.info(f"Current drawdown: {drawdown*100:.2f}% (Limit: {self.limits.max_drawdown_pct*100}%)")
        
        return is_acceptable, drawdown
    
    def check_daily_loss_limit(self) -> Tuple[bool, float]:
        """
        Check if daily loss limit is breached.
        
        Returns:
            (can_trade, daily_loss_percentage)
        """
        daily_loss_pct = abs(self.daily_pnl / self.portfolio_value)
        
        can_trade = daily_loss_pct < self.limits.max_daily_loss_pct
        
        if not can_trade:
            logger.warning(f"Daily loss limit breached: {daily_loss_pct*100:.2f}%")
        
        return can_trade, daily_loss_pct
    
    def check_correlation(
        self,
        new_ticker: str,
        price_data: Dict[str, pd.Series]
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Check correlation of new position with existing positions.
        
        Args:
            new_ticker: Ticker of new position
            price_data: Dict of ticker -> price series
            
        Returns:
            (is_acceptable, correlation_dict)
        """
        if not self.positions or new_ticker not in price_data:
            return True, {}
        
        correlations = {}
        
        for pos in self.positions:
            if pos.ticker not in price_data:
                continue
            
            # Calculate correlation
            corr = price_data[new_ticker].corr(price_data[pos.ticker])
            correlations[pos.ticker] = corr
            
            if abs(corr) > self.limits.max_correlation:
                logger.warning(
                    f"High correlation detected: {new_ticker} vs {pos.ticker} = {corr:.2f}"
                )
                return False, correlations
        
        return True, correlations
    
    def check_sector_exposure(
        self,
        new_sector: str,
        new_position_value: float
    ) -> Tuple[bool, float]:
        """
        Check if adding new position violates sector concentration limits.
        
        Args:
            new_sector: Sector of new position
            new_position_value: Value of new position
            
        Returns:
            (is_acceptable, sector_exposure_percentage)
        """
        # Calculate current sector exposure
        sector_exposure = {}
        for pos in self.positions:
            sector_exposure[pos.sector] = sector_exposure.get(pos.sector, 0) + pos.current_value
        
        # Add new position
        total_sector_value = sector_exposure.get(new_sector, 0) + new_position_value
        
        total_portfolio_value = self.portfolio_value + sum(pos.pnl for pos in self.positions)
        sector_pct = total_sector_value / total_portfolio_value
        
        is_acceptable = sector_pct <= self.limits.max_sector_exposure
        
        if not is_acceptable:
            logger.warning(
                f"Sector exposure limit breached for {new_sector}: {sector_pct*100:.2f}%"
            )
        
        return is_acceptable, sector_pct
    
    def validate_trade(
        self,
        ticker: str,
        entry_price: float,
        stop_loss: float,
        target: float,
        sector: str,
        quantity: int,
        volatility: float = 0.02,
        price_data: Optional[Dict[str, pd.Series]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Comprehensive trade validation against all risk rules.
        
        Args:
            ticker: Stock ticker
            entry_price: Proposed entry price
            stop_loss: Stop loss price
            target: Profit target price
            sector: Stock sector
            quantity: Proposed position size
            volatility: Stock volatility
            price_data: Historical price data for correlation check
            
        Returns:
            (is_valid, list_of_violations)
        """
        violations = []
        
        # 1. Check max open positions
        if len(self.positions) >= self.limits.max_open_positions:
            violations.append(f"Max open positions reached ({self.limits.max_open_positions})")
        
        # 2. Check daily loss limit
        can_trade, daily_loss = self.check_daily_loss_limit()
        if not can_trade:
            violations.append(f"Daily loss limit breached: {daily_loss*100:.2f}%")
        
        # 3. Check drawdown
        drawdown_ok, drawdown = self.check_drawdown()
        if not drawdown_ok:
            violations.append(f"Drawdown limit breached: {drawdown*100:.2f}%")
        
        # 4. Check risk/reward ratio
        risk = abs(entry_price - stop_loss)
        reward = abs(target - entry_price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        if rr_ratio < self.limits.min_risk_reward:
            violations.append(f"Risk/Reward ratio too low: {rr_ratio:.2f}")
        
        # 5. Check portfolio heat
        position_risk = risk * quantity
        heat_ok, heat = self.check_portfolio_heat(position_risk)
        if not heat_ok:
            violations.append(f"Portfolio heat limit breached: {heat:.2f}%")
        
        # 6. Check sector exposure
        position_value = entry_price * quantity
        sector_ok, sector_exp = self.check_sector_exposure(sector, position_value)
        if not sector_ok:
            violations.append(f"Sector exposure limit breached: {sector_exp*100:.2f}%")
        
        # 7. Check correlation
        if price_data:
            corr_ok, correlations = self.check_correlation(ticker, price_data)
            if not corr_ok:
                violations.append(f"High correlation with existing positions")
        
        is_valid = len(violations) == 0
        
        if not is_valid:
            logger.warning(f"Trade validation failed for {ticker}:")
            for violation in violations:
                logger.warning(f"  - {violation}")
        else:
            logger.info(f"Trade validation passed for {ticker}")
        
        return is_valid, violations
    
    def add_position(self, position: Position):
        """Add a new position to tracking"""
        self.positions.append(position)
        logger.info(f"Added position: {position.ticker}")
    
    def remove_position(self, ticker: str) -> Optional[Position]:
        """Remove a position from tracking"""
        for i, pos in enumerate(self.positions):
            if pos.ticker == ticker:
                removed = self.positions.pop(i)
                logger.info(f"Removed position: {ticker}")
                return removed
        return None
    
    def update_daily_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
    
    def reset_daily_metrics(self):
        """Reset daily metrics (call at end of day)"""
        self.daily_pnl = 0.0
        logger.info("Daily metrics reset")
    
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        heat_ok, heat = self.check_portfolio_heat()
        dd_ok, drawdown = self.check_drawdown()
        daily_ok, daily_loss = self.check_daily_loss_limit()
        
        total_value = self.portfolio_value + sum(pos.pnl for pos in self.positions)
        
        return {
            'portfolio_value': self.portfolio_value,
            'current_value': total_value,
            'open_positions': len(self.positions),
            'portfolio_heat': f"{heat:.2f}%",
            'drawdown': f"{drawdown*100:.2f}%",
            'daily_pnl': self.daily_pnl,
            'daily_loss_pct': f"{daily_loss*100:.2f}%",
            'peak_value': self.peak_portfolio_value,
            'limits': {
                'max_positions': self.limits.max_open_positions,
                'max_heat': f"{self.limits.max_portfolio_heat*100}%",
                'max_drawdown': f"{self.limits.max_drawdown_pct*100}%",
                'max_daily_loss': f"{self.limits.max_daily_loss_pct*100}%"
            },
            'status': {
                'heat_ok': heat_ok,
                'drawdown_ok': dd_ok,
                'daily_limit_ok': daily_ok
            }
        }
