"""
Test Signal Injector - Force signals for validation
Only works in paper mode for safety
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TestSignalInjector:
    """Inject test signals to validate execution pipeline"""
    
    def __init__(self, bot_engine):
        self.bot_engine = bot_engine
    
    def inject_breakout_signal(self, symbol: str = "RELIANCE") -> Dict:
        """
        Inject a fake breakout signal for testing
        
        Args:
            symbol: Stock symbol to create test signal for
        
        Returns: Signal data dict
        """
        if self.bot_engine.trading_mode != 'paper':
            raise ValueError("Test signals only work in PAPER mode!")
        
        # Get current price
        with self.bot_engine._lock:
            current_price = self.bot_engine.latest_prices.get(symbol, 2500.0)
        
        if current_price == 2500.0:
            logger.warning(f"⚠️  No live price for {symbol}, using default ₹2500.0")
        
        test_signal = {
            'symbol': symbol,
            'direction': 'up',
            'entry_price': current_price,
            'stop_loss': current_price * 0.98,  # 2% SL
            'target': current_price * 1.05,     # 5% target (2.5:1 RR)
            'quantity': 1,
            'reason': '🧪 TEST_SIGNAL_INJECTED',
            'confidence': 0.85,
            'bypass_screening': True  # Force through all filters
        }
        
        logger.warning(f"🧪 TEST SIGNAL INJECTED: {symbol} @ ₹{current_price:.2f}")
        logger.warning(f"   SL: ₹{test_signal['stop_loss']:.2f}, Target: ₹{test_signal['target']:.2f}")
        
        return test_signal
    
    def inject_via_api(self, signal_data: Dict) -> bool:
        """
        Inject custom signal via API
        
        Args:
            signal_data: Custom signal parameters
        
        Returns: Success boolean
        """
        try:
            # Validate signal
            required = ['symbol', 'direction', 'entry_price', 'stop_loss', 'target', 'quantity']
            if not all(k in signal_data for k in required):
                logger.error(f"Invalid signal data: {signal_data}")
                logger.error(f"Missing fields: {[k for k in required if k not in signal_data]}")
                return False
            
            # Force through execution
            signal_data['bypass_screening'] = True
            signal_data['reason'] = signal_data.get('reason', 'API_INJECTED_SIGNAL')
            
            # Place order via bot engine
            self.bot_engine._place_entry_order(
                symbol=signal_data['symbol'],
                direction=signal_data['direction'],
                entry_price=signal_data['entry_price'],
                stop_loss=signal_data['stop_loss'],
                target=signal_data['target'],
                quantity=signal_data.get('quantity', 1),
                reason=signal_data['reason'],
                ml_signal_id=None,
                confidence=signal_data.get('confidence', 0.80),
                bypass_screening=signal_data.get('bypass_screening', False)
            )
            
            logger.info(f"✅ Test signal injected successfully: {signal_data['symbol']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to inject test signal: {e}", exc_info=True)
            return False
