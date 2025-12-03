"""
Simple Position Manager for Trading Bot
Lightweight position tracking without complex dependencies
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SimplePositionManager:
    """
    Simple position manager for tracking open positions.
    No external dependencies, no complex config files.
    """
    
    def __init__(self):
        """Initialize position manager with empty position dict"""
        self.positions: Dict[str, Dict[str, Any]] = {}
        logger.info("SimplePositionManager initialized")
    
    def add_position(self, symbol: str, entry_price: float, quantity: int, 
                     stop_loss: float, target: float, order_id: str = None,
                     ml_signal_id: str = None, **kwargs):
        """
        Add a new position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            quantity: Number of shares
            stop_loss: Stop loss price
            target: Target price
            order_id: Order ID from broker
            ml_signal_id: ML signal ID for tracking
            **kwargs: Additional metadata
        """
        position = {
            'symbol': symbol,
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'target': target,
            'order_id': order_id or f"POS_{symbol}_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now(),
            'status': 'open'
        }
        
        if ml_signal_id:
            position['ml_signal_id'] = ml_signal_id
        
        # Add any additional metadata
        position.update(kwargs)
        
        self.positions[symbol] = position
        logger.info(f"Position added: {symbol} @ ₹{entry_price:.2f} (SL: {stop_loss:.2f}, Target: {target:.2f})")
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all open positions.
        
        Returns:
            Dictionary of symbol -> position data
        """
        return self.positions.copy()
    
    def has_position(self, symbol: str) -> bool:
        """
        Check if a position exists for the symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if position exists, False otherwise
        """
        return symbol in self.positions
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position data for a specific symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Position dict or None
        """
        return self.positions.get(symbol)
    
    def remove_position(self, symbol: str) -> bool:
        """
        Remove a position (used when closing).
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if removed, False if didn't exist
        """
        if symbol in self.positions:
            del self.positions[symbol]
            logger.info(f"Position removed: {symbol}")
            return True
        return False
    
    def close_position(self, symbol: str) -> bool:
        """
        Close a position (alias for remove_position).
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if closed, False if didn't exist
        """
        return self.remove_position(symbol)
    
    def update_stop_loss(self, symbol: str, new_stop_loss: float):
        """
        Update stop loss for a position (trailing stop).
        
        Args:
            symbol: Trading symbol
            new_stop_loss: New stop loss price
        """
        if symbol in self.positions:
            old_sl = self.positions[symbol]['stop_loss']
            self.positions[symbol]['stop_loss'] = new_stop_loss
            logger.info(f"Updated SL for {symbol}: ₹{old_sl:.2f} -> ₹{new_stop_loss:.2f}")
    
    def get_position_count(self) -> int:
        """
        Get count of open positions.
        
        Returns:
            Number of open positions
        """
        return len(self.positions)
    
    def clear_all_positions(self):
        """Clear all positions (use with caution)"""
        count = len(self.positions)
        self.positions.clear()
        logger.warning(f"Cleared all positions ({count} removed)")
