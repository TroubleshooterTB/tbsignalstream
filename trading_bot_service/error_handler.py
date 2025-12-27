"""
Error Handler - Decorators and Utilities for Error Handling
Created: Dec 28, 2025
Purpose: Provide comprehensive error handling with retry logic and logging
"""

import functools
import time
import traceback
from typing import Callable, Any, Optional
from bot_errors import (
    BotError, CriticalError, RecoverableError, WarningError,
    classify_error, format_error_message
)


class ErrorHandler:
    """
    Centralized error handler with retry logic and logging
    """
    
    def __init__(self, activity_logger=None, max_retries: int = 3, 
                 retry_delay: float = 1.0):
        self.activity_logger = activity_logger
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_counts = {
            "critical": 0,
            "recoverable": 0,
            "warning": 0
        }
        self.last_errors = []  # Store last 50 errors
        self.max_error_history = 50
    
    def log(self, message: str, level: str = "INFO"):
        """Log message to activity feed"""
        if self.activity_logger:
            self.activity_logger.log_activity(message, level=level)
        else:
            print(f"[{level}] {message}")
    
    def record_error(self, error: Exception):
        """Record error in history"""
        severity, category = classify_error(error)
        self.error_counts[severity] = self.error_counts.get(severity, 0) + 1
        
        error_record = {
            "timestamp": time.time(),
            "severity": severity,
            "category": category,
            "message": str(error),
            "formatted": format_error_message(error)
        }
        
        self.last_errors.append(error_record)
        if len(self.last_errors) > self.max_error_history:
            self.last_errors.pop(0)
    
    def handle_error(self, error: Exception, context: str = "", 
                    retry_func: Optional[Callable] = None) -> tuple[bool, Any]:
        """
        Handle error based on type
        Returns: (should_continue, result)
        """
        self.record_error(error)
        formatted_msg = format_error_message(error)
        
        if isinstance(error, CriticalError):
            # Critical - log and stop
            self.log(f"{formatted_msg} | Context: {context}", level="ERROR")
            self.log("🛑 Bot must stop due to critical error", level="ERROR")
            return (False, None)
        
        elif isinstance(error, RecoverableError):
            # Recoverable - log and retry
            self.log(f"{formatted_msg} | Context: {context}", level="WARNING")
            
            if retry_func:
                result = self._retry_with_backoff(retry_func, error)
                if result is not None:
                    self.log(f"✅ Recovered from error after retry", level="INFO")
                    return (True, result)
                else:
                    self.log(f"❌ Failed to recover after {self.max_retries} retries", 
                           level="ERROR")
                    return (False, None)
            else:
                self.log("⏭️ Continuing without retry (no retry function)", level="INFO")
                return (True, None)
        
        elif isinstance(error, WarningError):
            # Warning - log and continue
            self.log(f"{formatted_msg} | Context: {context}", level="WARNING")
            return (True, None)
        
        else:
            # Unknown error - treat as critical
            self.log(f"❌ [UNKNOWN ERROR] {str(error)} | Context: {context}", 
                   level="ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", level="ERROR")
            return (False, None)
    
    def _retry_with_backoff(self, func: Callable, original_error: Exception) -> Any:
        """
        Retry function with exponential backoff
        """
        for attempt in range(1, self.max_retries + 1):
            delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
            
            self.log(f"🔄 Retry attempt {attempt}/{self.max_retries} in {delay:.1f}s...", 
                   level="INFO")
            time.sleep(delay)
            
            try:
                result = func()
                return result
            except Exception as e:
                if attempt == self.max_retries:
                    self.log(f"❌ Final retry attempt failed: {str(e)}", level="ERROR")
                    return None
                else:
                    self.log(f"⚠️ Retry {attempt} failed: {str(e)}", level="WARNING")
        
        return None
    
    def get_error_summary(self) -> dict:
        """Get summary of errors encountered"""
        return {
            "error_counts": self.error_counts,
            "recent_errors": self.last_errors[-10:] if self.last_errors else [],
            "total_errors": sum(self.error_counts.values())
        }


# ============================================================================
# DECORATORS
# ============================================================================

def with_error_handling(error_handler: ErrorHandler, context: str = "",
                       retry_on_failure: bool = False):
    """
    Decorator to add error handling to any function
    
    Usage:
        @with_error_handling(error_handler, context="WebSocket connection", retry_on_failure=True)
        def connect_websocket():
            # ... connection logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retry_func = lambda: func(*args, **kwargs) if retry_on_failure else None
                should_continue, result = error_handler.handle_error(
                    e, context=context or func.__name__, retry_func=retry_func
                )
                
                if not should_continue:
                    raise CriticalError(
                        f"Critical error in {func.__name__}",
                        details={"original_error": str(e)}
                    )
                
                return result
        
        return wrapper
    return decorator


def safe_execute(error_handler: ErrorHandler, default_return: Any = None):
    """
    Decorator to safely execute function and return default on error
    Never raises exception - always returns default or result
    
    Usage:
        @safe_execute(error_handler, default_return=[])
        def get_symbols():
            # ... may fail
            return symbols
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.record_error(e)
                error_handler.log(
                    f"⚠️ {func.__name__} failed: {str(e)} - returning default",
                    level="WARNING"
                )
                return default_return
        
        return wrapper
    return decorator


def log_exceptions(error_handler: ErrorHandler):
    """
    Decorator to log exceptions but re-raise them
    Use when you want to log but not handle the error
    
    Usage:
        @log_exceptions(error_handler)
        def critical_function():
            # ... will log error but still raise it
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.record_error(e)
                error_handler.log(
                    format_error_message(e) + f" in {func.__name__}",
                    level="ERROR"
                )
                raise  # Re-raise the exception
        
        return wrapper
    return decorator


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

class ErrorContext:
    """
    Context manager for error handling
    
    Usage:
        with ErrorContext(error_handler, "Database operation"):
            # ... code that may fail
            db.write()
    """
    
    def __init__(self, error_handler: ErrorHandler, context: str,
                 suppress_errors: bool = False):
        self.error_handler = error_handler
        self.context = context
        self.suppress_errors = suppress_errors
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            should_continue, _ = self.error_handler.handle_error(
                exc_val, context=self.context
            )
            
            if self.suppress_errors:
                return True  # Suppress the exception
            
            return should_continue  # Let exception propagate if critical
        
        return True
