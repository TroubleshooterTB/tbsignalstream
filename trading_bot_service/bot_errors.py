"""
Bot Error Classes - Comprehensive Error Hierarchy
Created: Dec 28, 2025
Purpose: Define all error types for proper error handling and recovery
"""

class BotError(Exception):
    """Base class for all bot errors"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self):
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class CriticalError(BotError):
    """
    Bot must stop immediately - cannot recover
    Examples: Invalid credentials, Firebase connection lost, corrupted data
    """
    pass


class RecoverableError(BotError):
    """
    Bot can continue after retry with backoff
    Examples: Temporary network issues, API rate limits, WebSocket disconnect
    """
    pass


class WarningError(BotError):
    """
    Log but continue normal operation
    Examples: Slow data fetch, missing single candle, high memory usage
    """
    pass


# ============================================================================
# SPECIFIC ERROR TYPES
# ============================================================================

# WebSocket Errors
class WebSocketError(RecoverableError):
    """WebSocket connection issues"""
    pass


class WebSocketDisconnected(WebSocketError):
    """WebSocket disconnected - will auto-reconnect"""
    pass


class WebSocketTimeout(WebSocketError):
    """No heartbeat received from WebSocket"""
    pass


class InvalidWebSocketData(WarningError):
    """Received invalid data from WebSocket"""
    pass


# API Errors
class APIError(RecoverableError):
    """Angel One API issues"""
    pass


class TokenExpired(CriticalError):
    """Authentication token expired - need to re-login"""
    pass


class RateLimitExceeded(RecoverableError):
    """API rate limit hit - need to wait"""
    pass


class NetworkTimeout(RecoverableError):
    """Network request timed out"""
    pass


class InvalidAPIResponse(WarningError):
    """API returned unexpected response"""
    pass


# Data Processing Errors
class DataError(WarningError):
    """Data processing issues"""
    pass


class MissingCandleData(DataError):
    """Required candle data not available"""
    pass


class InvalidPriceData(DataError):
    """Price data is invalid or corrupted"""
    pass


class PatternDetectionError(WarningError):
    """Error during pattern detection - continue with next symbol"""
    pass


class CalculationError(WarningError):
    """Math calculation error (division by zero, etc.)"""
    pass


# Order Errors
class OrderError(RecoverableError):
    """Order placement issues"""
    pass


class InsufficientMargin(OrderError):
    """Not enough margin to place order"""
    pass


class InvalidOrderParams(OrderError):
    """Order parameters are invalid"""
    pass


class BrokerRejection(OrderError):
    """Broker rejected the order"""
    pass


class OrderNetworkError(RecoverableError):
    """Network error during order placement"""
    pass


# Internal Bot Errors
class BotInternalError(CriticalError):
    """Internal bot logic errors"""
    pass


class StrategyInitError(CriticalError):
    """Strategy failed to initialize"""
    pass


class MemoryError(WarningError):
    """High memory usage detected"""
    pass


class ThreadError(CriticalError):
    """Threading issue detected"""
    pass


class FirestoreError(RecoverableError):
    """Firestore write/read failed"""
    pass


class ConfigurationError(CriticalError):
    """Bot configuration is invalid"""
    pass


# ============================================================================
# ERROR UTILITIES
# ============================================================================

def classify_error(error: Exception) -> tuple[str, str]:
    """
    Classify any error into severity level and category
    Returns: (severity, category)
    severity: "critical" | "recoverable" | "warning"
    category: error type name
    """
    if isinstance(error, CriticalError):
        return ("critical", error.__class__.__name__)
    elif isinstance(error, RecoverableError):
        return ("recoverable", error.__class__.__name__)
    elif isinstance(error, WarningError):
        return ("warning", error.__class__.__name__)
    else:
        # Unknown error - treat as critical
        return ("critical", "UnknownError")


def get_error_emoji(severity: str) -> str:
    """Get emoji for error severity"""
    emoji_map = {
        "critical": "🔴",
        "recoverable": "🟡",
        "warning": "⚠️",
        "info": "ℹ️"
    }
    return emoji_map.get(severity, "❌")


def format_error_message(error: Exception, include_details: bool = True) -> str:
    """
    Format error message for logging
    """
    if isinstance(error, BotError):
        severity, category = classify_error(error)
        emoji = get_error_emoji(severity)
        
        message = f"{emoji} [{severity.upper()}] {category}: {error.message}"
        
        if include_details and error.details:
            details_str = ", ".join([f"{k}={v}" for k, v in error.details.items()])
            message += f" ({details_str})"
        
        return message
    else:
        # Standard exception
        return f"❌ [ERROR] {error.__class__.__name__}: {str(error)}"
