"""
Production Hardening - Phase 5
Error handling, retry logic, health monitoring
"""

import logging
from typing import Callable, Any, Optional
from functools import wraps
import time
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker pattern for API calls
    Prevents cascading failures by stopping calls after repeated failures
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds before trying again
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED = working, OPEN = broken, HALF_OPEN = testing
    
    def call(self, func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """
        Execute function with circuit breaker protection
        
        Returns:
            (success: bool, result: Any)
        """
        # If circuit is OPEN, check if timeout has passed
        if self.state == 'OPEN':
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.timeout:
                self.state = 'HALF_OPEN'
                logger.info("🔄 Circuit breaker entering HALF_OPEN state (testing)")
            else:
                logger.warning("⚡ Circuit breaker OPEN - call blocked")
                return False, None
        
        # Try to execute
        try:
            result = func(*args, **kwargs)
            
            # Success - reset circuit
            if self.state in ['HALF_OPEN', 'CLOSED']:
                if self.failure_count > 0:
                    logger.info(f"✅ Circuit breaker recovered (was at {self.failure_count} failures)")
                self.failure_count = 0
                self.state = 'CLOSED'
            
            return True, result
            
        except Exception as e:
            logger.error(f"Circuit breaker caught exception: {e}")
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            # Trip circuit if threshold exceeded
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logger.error(f"⚡ Circuit breaker OPEN after {self.failure_count} failures")
            
            return False, None
    
    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.state = 'CLOSED'
        logger.info("✅ Circuit breaker manually reset")


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
    """
    Decorator for exponential backoff retry logic
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = base_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"❌ {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    # Calculate next delay (exponential backoff with jitter)
                    delay = min(delay * 2, max_delay)
                    actual_delay = delay * (0.5 + 0.5 * time.time() % 1)  # Add jitter
                    
                    logger.warning(
                        f"⚠️ {func.__name__} attempt {attempt + 1}/{max_retries} failed: {e}. "
                        f"Retrying in {actual_delay:.1f}s..."
                    )
                    time.sleep(actual_delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class HealthMonitor:
    """Monitor system health and send alerts"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.error_count = 0
        self.warning_count = 0
        self.last_health_check = datetime.now()
        self.health_status = 'HEALTHY'  # HEALTHY, DEGRADED, CRITICAL
        
        self.metrics = {
            'total_signals': 0,
            'accepted_signals': 0,
            'rejected_signals': 0,
            'total_trades': 0,
            'api_calls': 0,
            'api_failures': 0,
            'websocket_disconnects': 0
        }
    
    def record_signal(self, accepted: bool):
        """Record signal generation"""
        self.metrics['total_signals'] += 1
        if accepted:
            self.metrics['accepted_signals'] += 1
        else:
            self.metrics['rejected_signals'] += 1
    
    def record_trade(self):
        """Record trade execution"""
        self.metrics['total_trades'] += 1
    
    def record_api_call(self, success: bool):
        """Record API call"""
        self.metrics['api_calls'] += 1
        if not success:
            self.metrics['api_failures'] += 1
    
    def record_websocket_disconnect(self):
        """Record WebSocket disconnect"""
        self.metrics['websocket_disconnects'] += 1
    
    def record_error(self):
        """Record error"""
        self.error_count += 1
        
        # Update health status
        if self.error_count >= 50:
            self.health_status = 'CRITICAL'
        elif self.error_count >= 20:
            self.health_status = 'DEGRADED'
    
    def record_warning(self):
        """Record warning"""
        self.warning_count += 1
    
    def get_health_report(self) -> dict:
        """Get comprehensive health report"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate rates
        signal_acceptance_rate = 0
        if self.metrics['total_signals'] > 0:
            signal_acceptance_rate = self.metrics['accepted_signals'] / self.metrics['total_signals']
        
        api_success_rate = 1.0
        if self.metrics['api_calls'] > 0:
            api_success_rate = 1 - (self.metrics['api_failures'] / self.metrics['api_calls'])
        
        return {
            'status': self.health_status,
            'uptime_seconds': uptime,
            'uptime_formatted': self._format_uptime(uptime),
            'errors': self.error_count,
            'warnings': self.warning_count,
            'metrics': {
                **self.metrics,
                'signal_acceptance_rate': f"{signal_acceptance_rate*100:.1f}%",
                'api_success_rate': f"{api_success_rate*100:.1f}%"
            },
            'last_check': self.last_health_check.isoformat()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        return self.health_status == 'HEALTHY'


def safe_execute(func: Callable, default_return: Any = None, log_errors: bool = True) -> Any:
    """
    Safely execute a function, catching all exceptions
    
    Args:
        func: Function to execute
        default_return: Value to return if exception occurs
        log_errors: Whether to log errors
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Error in {func.__name__ if hasattr(func, '__name__') else 'function'}: {e}")
            logger.debug(traceback.format_exc())
        return default_return


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_proceed(self) -> bool:
        """Check if call is allowed"""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if under limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def wait_time(self) -> float:
        """Get time to wait before next call is allowed"""
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return self.time_window - (time.time() - oldest_call)


# Global instances
api_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
health_monitor = HealthMonitor()
api_rate_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 calls per minute
