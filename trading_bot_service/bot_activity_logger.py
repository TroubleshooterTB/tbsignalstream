"""
Bot Activity Logger - Logs real-time analysis steps to Firestore for dashboard visibility
ENHANCED: Now with transparent verbose logging for complete bot visibility
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from firebase_admin import firestore

logger = logging.getLogger(__name__)


class BotActivityLogger:
    """
    Logs bot analysis activities to Firestore for real-time dashboard monitoring.
    
    ENHANCED FEATURES:
    - Verbose mode toggle (show every action or just important ones)
    - Scan progress tracking
    - WebSocket status logging
    - Performance metrics logging
    - Complete transparency into bot operations
    
    Activities include:
    - Pattern detections (even if they fail screening)
    - Confidence scores and R:R ratios
    - 24-level screening results
    - 27-level validation results
    - Final signal generation/rejection
    - Scan cycles and progress
    - WebSocket connection status
    - Data fetching status
    - Performance metrics
    """
    
    def __init__(self, user_id: str, db_client=None, verbose_mode: bool = True):
        """
        Initialize the activity logger.
        
        Args:
            user_id: User ID for activity tracking
            db_client: Firestore client (optional, will create if not provided)
            verbose_mode: If True, logs every action. If False, only important events.
        """
        self.user_id = user_id
        self.db = db_client
        self.collection = None
        self.firestore_available = False
        
        # Try to initialize Firestore collection
        try:
            if self.db:
                self.collection = self.db.collection('bot_activity')
                self.firestore_available = True
            else:
                logger.warning(f"⚠️ BotActivityLogger initialized without Firestore - logging disabled for user {user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot activity logger: {e}")
            self.firestore_available = False
        
        self.verbose = verbose_mode  # User can toggle this
        self._last_log_time = {}  # Throttle frequent logs
        logger.info(f"BotActivityLogger initialized for user: {user_id} (Verbose: {verbose_mode})")
    
    def set_verbose_mode(self, enabled: bool):
        """Enable or disable verbose logging"""
        self.verbose = enabled
        logger.info(f"Verbose mode {'ENABLED' if enabled else 'DISABLED'}")
    
    def _should_throttle(self, key: str, seconds: float = 1.0) -> bool:
        """
        Check if we should throttle this log entry
        Prevents flooding Firestore with duplicate messages
        """
        now = datetime.now().timestamp()
        last_time = self._last_log_time.get(key, 0)
        if now - last_time < seconds:
            return True
        self._last_log_time[key] = now
        return False
    
    def log_activity(self, message: str, level: str = "INFO", symbol: str = "SYSTEM",
                     details: Optional[Dict] = None, throttle_key: Optional[str] = None):
        """
        Generic activity logging method.
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            symbol: Stock symbol or SYSTEM
            details: Additional details dictionary
            throttle_key: If provided, throttle duplicate messages
        """
        # If Firestore unavailable, log to console only
        if not self.firestore_available or not self.collection:
            logger.info(f"[{level}] {symbol}: {message}")
            return
        
        try:
            # Skip DEBUG logs if not in verbose mode
            if level == "DEBUG" and not self.verbose:
                return
            
            # Throttle if requested
            if throttle_key and self._should_throttle(throttle_key):
                return
            
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'activity',
                'level': level,
                'symbol': symbol,
                'message': message,
                'details': details or {}
            }
            
            self.collection.add(activity)
            
        except Exception as e:
            logger.error(f"Failed to log activity to Firestore: {e}")
            # Log to console as fallback
            logger.info(f"[{level}] {symbol}: {message}")
    
    def log_bot_started(self, mode: str, strategy: str, symbols_count: int):
        """Log when bot starts"""
        try:
            logger.info(f"📝 [LOGGER] log_bot_started called - mode: {mode}, strategy: {strategy}, symbols: {symbols_count}")
            logger.info(f"📝 [LOGGER] User ID: {self.user_id}, Firestore: {self.firestore_available}, Collection: {self.collection is not None}")
            
            if not self.firestore_available or not self.collection:
                logger.error(f"❌ [LOGGER] Cannot log bot start - Firestore not available or collection is None")
                logger.error(f"❌ [LOGGER] Check: 1) Firebase initialized, 2) Firestore client created, 3) Collection name correct")
                return
            
            activity = {
                'user_id': self.user_id,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'type': 'bot_started',
                'symbol': 'SYSTEM',
                'message': f"🚀 Bot STARTED | Mode: {mode.upper()} | Strategy: {strategy} | Symbols: {symbols_count}",
                'level': 'INFO',
                'details': {'mode': mode, 'strategy': strategy, 'symbols_count': symbols_count}
            }
            
            logger.info(f"📝 [LOGGER] Activity document prepared, attempting Firestore write...")
            logger.info(f"📝 [LOGGER] Collection path: bot_activity, User ID: {self.user_id}")
            doc_ref = self.collection.add(activity)
            logger.info(f"✅ [LOGGER] Bot start logged successfully! Document ID: {doc_ref[1].id}")
            logger.info(f"✅ [LOGGER] Dashboard activity feed should now show: 🚀 Bot STARTED")
            
        except Exception as e:
            logger.error(f"❌ [LOGGER] CRITICAL: Failed to log bot start: {e}", exc_info=True)
            logger.error(f"❌ [LOGGER] This means activity feed will be empty. Check Firestore permissions.")
            # Re-raise to alert caller that logging failed
            raise
    
    def log_websocket_status(self, status: str, details: Optional[Dict] = None):
        """Log WebSocket connection status changes"""
        emoji = "🟢" if status == "connected" else "🔴" if status == "disconnected" else "🟡"
        self.log_activity(
            f"{emoji} WebSocket {status.upper()}",
            level="INFO" if status == "connected" else "WARNING",
            details=details
        )
    
    def log_data_fetch(self, symbol: str, success: bool, time_taken: float,
                       candles_count: Optional[int] = None):
        """Log data fetching for a symbol"""
        if success:
            if time_taken > 3.0:
                self.log_activity(
                    f"🐌 Slow data fetch for {symbol} ({time_taken:.1f}s)",
                    level="WARNING",
                    symbol=symbol,
                    details={'time_taken': time_taken, 'candles': candles_count}
                )
            elif self.verbose:
                self.log_activity(
                    f"✅ Data fetched for {symbol} ({time_taken:.1f}s, {candles_count} candles)",
                    level="DEBUG",
                    symbol=symbol,
                    details={'time_taken': time_taken, 'candles': candles_count}
                )
        else:
            self.log_activity(
                f"❌ Failed to fetch data for {symbol}",
                level="ERROR",
                symbol=symbol,
                details={'time_taken': time_taken}
            )
    
    def log_scan_progress(self, current: int, total: int, symbol: str):
        """Log scan progress (only in verbose mode)"""
        if not self.verbose:
            return
        
        # Only log every 5th symbol to avoid spam
        if current % 5 == 0 or current == total:
            percentage = (current / total * 100) if total > 0 else 0
            self.log_activity(
                f"🔄 Scanning {symbol} ({current}/{total} - {percentage:.0f}%)",
                level="DEBUG",
                symbol=symbol,
                details={'current': current, 'total': total, 'percentage': percentage},
                throttle_key=f"scan_progress_{current // 5}"
            )
    
    def log_indicator_values(self, symbol: str, indicators: Dict):
        """Log current indicator values for a symbol"""
        if not self.verbose:
            return
        
        # Format indicator string
        indicator_str = ", ".join([f"{k.upper()}: {v:.2f}" for k, v in indicators.items() if isinstance(v, (int, float))])
        
        self.log_activity(
            f"📊 {symbol} indicators: {indicator_str}",
            level="DEBUG",
            symbol=symbol,
            details=indicators,
            throttle_key=f"indicators_{symbol}"
        )
    
    def log_pattern_analysis(self, symbol: str, patterns_found: int, best_pattern: Optional[str] = None):
        """Log pattern analysis results"""
        if patterns_found > 0:
            self.log_activity(
                f"🎯 {symbol}: Found {patterns_found} pattern(s) | Best: {best_pattern}",
                level="INFO",
                symbol=symbol,
                details={'patterns_found': patterns_found, 'best_pattern': best_pattern}
            )
        elif self.verbose:
            self.log_activity(
                f"❌ {symbol}: No patterns detected",
                level="DEBUG",
                symbol=symbol,
                details={'patterns_found': 0}
            )
    
    def log_screening_decision(self, symbol: str, pattern: str, passed: bool, 
                             reason: str, level_details: Optional[Dict] = None):
        """Log screening decision with reason"""
        emoji = "✅" if passed else "❌"
        message = f"{emoji} {symbol} {pattern}: {'PASSED' if passed else 'FAILED'} screening - {reason}"
        
        self.log_activity(
            message,
            level="INFO" if passed else "DEBUG",
            symbol=symbol,
            details={'pattern': pattern, 'passed': passed, 'reason': reason, 'levels': level_details}
        )
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str = ""):
        """Log performance metrics"""
        if not self.verbose:
            return
        
        self.log_activity(
            f"⏱️ {metric_name}: {value:.2f}{unit}",
            level="DEBUG",
            details={'metric': metric_name, 'value': value, 'unit': unit},
            throttle_key=f"perf_{metric_name}"
        )
    
    def log_error(self, error_message: str, context: str = "", severity: str = "ERROR"):
        """Log errors with context"""
        self.log_activity(
            f"🔴 {error_message}" + (f" | Context: {context}" if context else ""),
            level=severity,
            details={'context': context}
        )
    
    def log_order_placed(self, symbol: str, side: str, quantity: int, price: float,
                        order_id: Optional[str] = None):
        """Log order placement"""
        self.log_activity(
            f"💰 ORDER PLACED: {side.upper()} {quantity} {symbol} @ ₹{price:.2f}",
            level="INFO",
            symbol=symbol,
            details={
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_id': order_id
            }
        )
    
    def log_position_update(self, symbol: str, status: str, pnl: float, pnl_pct: float):
        """Log position updates"""
        emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        self.log_activity(
            f"{emoji} {symbol}: {status} | P&L: ₹{pnl:.2f} ({pnl_pct:+.2f}%)",
            level="INFO",
            symbol=symbol,
            details={
                'status': status,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            }
        )
    
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
            logger.info(f"📝 [LOGGER] Starting log_pattern_detected for {symbol}")
            logger.info(f"📝 [LOGGER] Firestore available: {self.firestore_available}")
            logger.info(f"📝 [LOGGER] Collection initialized: {self.collection is not None}")
            
            if not self.firestore_available or not self.collection:
                logger.error(f"❌ [LOGGER] Cannot log - Firestore not available or collection is None")
                return
            
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
            
            logger.info(f"📝 [LOGGER] Activity data prepared: {activity}")
            logger.info(f"📝 [LOGGER] Attempting Firestore write...")
            doc_ref = self.collection.add(activity)
            logger.info(f"✅ [LOGGER] Firestore write successful! Doc ID: {doc_ref[1].id}")
            logger.info(f"✅ [LOGGER] Pattern logged: {symbol} - {pattern} (Confidence: {confidence:.1f}%, R:R: {rr_ratio:.2f})")
            
        except Exception as e:
            logger.error(f"❌ [LOGGER] Failed to log pattern detection for {symbol}: {e}", exc_info=True)
            logger.error(f"❌ [LOGGER] Activity data was: {locals().get('activity', 'N/A')}")
    
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
            logger.info(f"📝 [LOGGER] log_scan_cycle_start called - total: {total_symbols}, with_data: {symbols_with_data}")
            logger.info(f"📝 [LOGGER] Firestore available: {self.firestore_available}, Collection: {self.collection is not None}")
            
            if not self.firestore_available or not self.collection:
                logger.error(f"❌ [LOGGER] Cannot log scan cycle - Firestore not available")
                return
            
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
            
            logger.info(f"📝 [LOGGER] Attempting Firestore write...")
            doc_ref = self.collection.add(activity)
            logger.info(f"✅ [LOGGER] Scan cycle logged! Doc ID: {doc_ref[1].id}")
            
        except Exception as e:
            logger.error(f"❌ [LOGGER] Failed to log scan cycle: {e}", exc_info=True)
    
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
