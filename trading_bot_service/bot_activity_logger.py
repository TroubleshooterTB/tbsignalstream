"""
Bot Activity Logger - Logs real-time analysis steps to Firestore for dashboard visibility
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class BotActivityLogger:
    """
    Logs bot analysis activities to Firestore for real-time dashboard monitoring.
    
    Activities include:
    - Pattern detections (even if they fail screening)
    - Confidence scores and R:R ratios
    - 24-level screening results
    - 27-level validation results
    - Final signal generation/rejection
    """
    
    def __init__(self, user_id: str, db_client=None):
        """
        Initialize the activity logger.
        
        Args:
            user_id: User ID for activity tracking
            db_client: Firestore client (optional, will create if not provided)
        """
        self.user_id = user_id
        self.db = db_client or firestore.client()
        self.collection = self.db.collection('bot_activity')
        logger.info(f"BotActivityLogger initialized for user: {user_id}")
    
    def log_pattern_detected(self, symbol: str, pattern: str, confidence: float, 
                            rr_ratio: float, details: Optional[Dict] = None):
        """
        Log when a pattern is detected (before screening/validation).
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name (e.g., "Bullish Engulfing")
            confidence: Confidence score (0-100)
            rr_ratio: Risk-reward ratio
            details: Additional pattern details
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'pattern_detected',
                'symbol': symbol,
                'pattern': pattern,
                'confidence': round(confidence, 2),
                'rr_ratio': round(rr_ratio, 2),
                'details': details or {}
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged pattern detection: {symbol} - {pattern}")
            
        except Exception as e:
            logger.error(f"Failed to log pattern detection: {e}")
    
    def log_screening_started(self, symbol: str, pattern: str):
        """Log when 24-level advanced screening starts."""
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'screening_started',
                'symbol': symbol,
                'pattern': pattern,
                'level': '24-Level Advanced Screening'
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged screening start: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log screening start: {e}")
    
    def log_screening_passed(self, symbol: str, pattern: str, reason: str, 
                            passed_levels: Optional[list] = None):
        """
        Log when screening passes.
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            reason: Why it passed
            passed_levels: List of levels that passed
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'screening_passed',
                'symbol': symbol,
                'pattern': pattern,
                'reason': reason,
                'level': '24-Level Advanced Screening',
                'details': {
                    'passed_levels': passed_levels or []
                }
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged screening pass: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log screening pass: {e}")
    
    def log_screening_failed(self, symbol: str, pattern: str, reason: str, 
                            failed_level: Optional[str] = None):
        """
        Log when screening fails.
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            reason: Why it failed
            failed_level: Which level failed
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'screening_failed',
                'symbol': symbol,
                'pattern': pattern,
                'reason': reason,
                'level': failed_level or '24-Level Advanced Screening'
            }
            
            self.collection.add(activity)
            logger.debug(f"❌ Logged screening fail: {symbol} - {reason}")
            
        except Exception as e:
            logger.error(f"Failed to log screening fail: {e}")
    
    def log_validation_started(self, symbol: str, pattern: str):
        """Log when 27-level validation starts."""
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'validation_started',
                'symbol': symbol,
                'pattern': pattern,
                'level': '27-Level Pattern Validation'
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged validation start: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log validation start: {e}")
    
    def log_validation_passed(self, symbol: str, pattern: str, 
                             validation_score: Optional[float] = None):
        """
        Log when validation passes.
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            validation_score: Validation score (0-100)
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'validation_passed',
                'symbol': symbol,
                'pattern': pattern,
                'level': '27-Level Pattern Validation',
                'details': {
                    'validation_score': validation_score
                } if validation_score else {}
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged validation pass: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log validation pass: {e}")
    
    def log_validation_failed(self, symbol: str, pattern: str, reason: str,
                             failed_level: Optional[str] = None):
        """
        Log when validation fails.
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            reason: Why it failed
            failed_level: Which validation level failed
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'validation_failed',
                'symbol': symbol,
                'pattern': pattern,
                'reason': reason,
                'level': failed_level or '27-Level Pattern Validation'
            }
            
            self.collection.add(activity)
            logger.debug(f"❌ Logged validation fail: {symbol} - {reason}")
            
        except Exception as e:
            logger.error(f"Failed to log validation fail: {e}")
    
    def log_signal_generated(self, symbol: str, pattern: str, confidence: float,
                            rr_ratio: float, entry_price: float, stop_loss: float,
                            profit_target: float):
        """
        Log when a final signal is generated (passed all checks).
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            confidence: Final confidence (0-100)
            rr_ratio: Risk-reward ratio
            entry_price: Entry price
            stop_loss: Stop loss price
            profit_target: Profit target price
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'signal_generated',
                'symbol': symbol,
                'pattern': pattern,
                'confidence': round(confidence, 2),
                'rr_ratio': round(rr_ratio, 2),
                'details': {
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'profit_target': profit_target
                }
            }
            
            self.collection.add(activity)
            logger.info(f"🎯 Logged signal generation: {symbol} @ ₹{entry_price}")
            
        except Exception as e:
            logger.error(f"Failed to log signal generation: {e}")
    
    def log_signal_rejected(self, symbol: str, pattern: str, reason: str,
                           confidence: Optional[float] = None, 
                           rr_ratio: Optional[float] = None):
        """
        Log when a signal is rejected (failed criteria).
        
        Args:
            symbol: Stock symbol
            pattern: Pattern name
            reason: Why it was rejected
            confidence: Confidence score if available
            rr_ratio: R:R ratio if available
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'signal_rejected',
                'symbol': symbol,
                'pattern': pattern,
                'reason': reason,
                'confidence': round(confidence, 2) if confidence else None,
                'rr_ratio': round(rr_ratio, 2) if rr_ratio else None
            }
            
            self.collection.add(activity)
            logger.debug(f"❌ Logged signal rejection: {symbol} - {reason}")
            
        except Exception as e:
            logger.error(f"Failed to log signal rejection: {e}")
    
    def cleanup_old_activities(self, hours: int = 24):
        """
        Remove activity logs older than specified hours.
        
        Args:
            hours: Number of hours to keep (default: 24)
        """
        try:
            cutoff = datetime.now().timestamp() - (hours * 3600)
            cutoff_dt = datetime.fromtimestamp(cutoff)
            
            # Query old activities
            old_activities = (
                self.collection
                .where('user_id', '==', self.user_id)
                .where('timestamp', '<', cutoff_dt)
                .stream()
            )
            
            # Delete in batch
            batch = self.db.batch()
            count = 0
            
            for doc in old_activities:
                batch.delete(doc.reference)
                count += 1
                
                if count >= 500:  # Firestore batch limit
                    batch.commit()
                    batch = self.db.batch()
                    count = 0
            
            if count > 0:
                batch.commit()
            
            logger.info(f"🧹 Cleaned up {count} old activity logs (older than {hours}h)")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old activities: {e}")
    
    def log_scan_cycle_start(self, total_symbols: int, symbols_with_data: int):
        """
        Log when a new scan cycle begins.
        
        Args:
            total_symbols: Total symbols to scan
            symbols_with_data: Number of symbols with sufficient data
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'scan_cycle_start',
                'symbol': 'SYSTEM',
                'reason': f'Scanning {symbols_with_data}/{total_symbols} symbols',
                'details': {
                    'total_symbols': total_symbols,
                    'symbols_with_data': symbols_with_data
                }
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged scan cycle start: {total_symbols} symbols")
            
        except Exception as e:
            logger.error(f"Failed to log scan cycle start: {e}")
    
    def log_symbol_scanning(self, symbol: str, current_price: float):
        """
        Log when scanning a specific symbol.
        
        Args:
            symbol: Stock symbol being scanned
            current_price: Current market price
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'symbol_scanning',
                'symbol': symbol,
                'reason': f'Analyzing {symbol} at ₹{current_price:.2f}',
                'details': {
                    'current_price': current_price
                }
            }
            
            self.collection.add(activity)
            logger.debug(f"✅ Logged symbol scan: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log symbol scan: {e}")
    
    def log_symbol_skipped(self, symbol: str, reason: str):
        """
        Log when a symbol is skipped during scanning.
        
        Args:
            symbol: Stock symbol that was skipped
            reason: Why it was skipped
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'symbol_skipped',
                'symbol': symbol,
                'reason': reason
            }
            
            self.collection.add(activity)
            logger.debug(f"⏭️  Logged symbol skip: {symbol} - {reason}")
            
        except Exception as e:
            logger.error(f"Failed to log symbol skip: {e}")
    
    def log_no_pattern(self, symbol: str, indicators: dict):
        """
        Log when no pattern is detected for a symbol.
        
        Args:
            symbol: Stock symbol
            indicators: Current indicator values (RSI, ADX, etc.)
        """
        try:
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'no_pattern',
                'symbol': symbol,
                'reason': f'No pattern detected (RSI: {indicators.get("rsi", 0):.1f}, ADX: {indicators.get("adx", 0):.1f})',
                'details': indicators
            }
            
            self.collection.add(activity)
            logger.debug(f"📊 Logged no pattern: {symbol}")
            
        except Exception as e:
            logger.error(f"Failed to log no pattern: {e}")
