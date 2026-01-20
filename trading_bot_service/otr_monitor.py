"""
Order-to-Trade Ratio (OTR) Monitor for SEBI Compliance
Tracks order activity to ensure compliance with SEBI regulations on algo trading noise
"""

import logging
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class OrderToTradeRatioMonitor:
    """
    Monitor OTR to ensure SEBI compliance.
    
    SEBI Requirement: OTR should not exceed 20:1
    High OTR indicates excessive market noise without execution.
    
    Formula: OTR = (Orders Placed + Orders Modified + Orders Cancelled) / Orders Executed
    """
    
    def __init__(self, otr_threshold: float = 20.0):
        self.otr_threshold = otr_threshold
        self.orders_placed = 0
        self.orders_modified = 0
        self.orders_cancelled = 0
        self.orders_executed = 0
        self.reset_time = datetime.now()
        self._throttle_enabled = False
        self._throttle_until = None
        
    def record_order_placed(self):
        """Record a new order placement"""
        self.orders_placed += 1
        self._check_otr()
        logger.debug(f"📊 OTR: Orders placed = {self.orders_placed}")
    
    def record_order_executed(self):
        """Record an order execution"""
        self.orders_executed += 1
        logger.debug(f"📊 OTR: Orders executed = {self.orders_executed}")
    
    def record_order_modified(self):
        """Record an order modification"""
        self.orders_modified += 1
        self._check_otr()
        logger.debug(f"📊 OTR: Orders modified = {self.orders_modified}")
    
    def record_order_cancelled(self):
        """Record an order cancellation"""
        self.orders_cancelled += 1
        self._check_otr()
        logger.debug(f"📊 OTR: Orders cancelled = {self.orders_cancelled}")
    
    def _check_otr(self):
        """Check if OTR exceeds threshold and trigger throttle if needed"""
        if self.orders_executed == 0:
            return  # Can't calculate OTR yet
        
        total_actions = self.orders_placed + self.orders_modified + self.orders_cancelled
        otr = total_actions / self.orders_executed
        
        if otr > self.otr_threshold:
            logger.critical(f"🚨 HIGH OTR WARNING: {otr:.1f}:1 (SEBI threshold: {self.otr_threshold}:1)")
            logger.critical(f"   Placed: {self.orders_placed} | Modified: {self.orders_modified}")
            logger.critical(f"   Cancelled: {self.orders_cancelled} | Executed: {self.orders_executed}")
            logger.critical("   🚫 THROTTLING: No new orders for 5 minutes (SEBI compliance)")
            
            # Enable throttle for 5 minutes
            self._throttle_enabled = True
            self._throttle_until = datetime.now().timestamp() + (5 * 60)
            
        elif otr > (self.otr_threshold * 0.75):  # 75% of threshold
            logger.warning(f"⚠️ Elevated OTR: {otr:.1f}:1 (approaching SEBI threshold: {self.otr_threshold}:1)")
    
    def is_throttled(self) -> bool:
        """Check if bot should throttle new orders due to high OTR"""
        if not self._throttle_enabled:
            return False
        
        # Check if throttle period has expired
        if self._throttle_until and datetime.now().timestamp() > self._throttle_until:
            logger.info("✅ OTR throttle period expired - resuming normal operation")
            self._throttle_enabled = False
            self._throttle_until = None
            return False
        
        return True
    
    def get_current_otr(self) -> float:
        """Get current OTR value"""
        if self.orders_executed == 0:
            return 0.0
        total_actions = self.orders_placed + self.orders_modified + self.orders_cancelled
        return total_actions / self.orders_executed
    
    def get_daily_report(self) -> Dict:
        """Get comprehensive daily OTR report"""
        total_actions = self.orders_placed + self.orders_modified + self.orders_cancelled
        otr = self.get_current_otr()
        
        return {
            'orders_placed': self.orders_placed,
            'orders_modified': self.orders_modified,
            'orders_cancelled': self.orders_cancelled,
            'orders_executed': self.orders_executed,
            'total_actions': total_actions,
            'otr_ratio': otr,
            'otr_threshold': self.otr_threshold,
            'compliant': otr <= self.otr_threshold,
            'throttled': self._throttle_enabled,
            'reset_time': self.reset_time.isoformat()
        }
    
    def reset_daily(self):
        """Reset counters for new trading day"""
        logger.info("📊 Resetting OTR counters for new trading day")
        self.orders_placed = 0
        self.orders_modified = 0
        self.orders_cancelled = 0
        self.orders_executed = 0
        self.reset_time = datetime.now()
        self._throttle_enabled = False
        self._throttle_until = None
