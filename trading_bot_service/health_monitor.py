"""
Health Monitor - Track Bot Health and Performance
Created: Dec 28, 2025
Purpose: Monitor bot health, performance metrics, and provide detailed status
"""

import time
import threading
import psutil
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class HealthMonitor:
    """
    Monitor bot health and performance metrics
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.lock = threading.Lock()
        
        # WebSocket health
        self.websocket_connected = False
        self.last_tick_time: Optional[float] = None
        self.reconnect_count = 0
        self.total_ticks_received = 0
        
        # Data health
        self.symbols_tracked = 0
        self.candles_loaded = 0
        self.missing_data_symbols = []
        self.last_scan_time: Optional[float] = None
        self.scan_cycle_times = []  # Last 10 scan times
        
        # Error tracking
        self.errors_last_hour = []
        self.critical_errors = 0
        self.recoverable_errors = 0
        self.warnings = 0
        
        # Performance metrics
        self.memory_usage_mb = 0
        self.cpu_percent = 0
        self.active_bots = 0
        
        # Trading metrics
        self.patterns_detected_today = 0
        self.orders_placed_today = 0
        self.last_pattern_time: Optional[float] = None
        self.last_order_time: Optional[float] = None
        
        # Start monitoring thread
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background thread for continuous monitoring"""
        def monitor_loop():
            while True:
                try:
                    self._update_system_metrics()
                    self._cleanup_old_errors()
                    time.sleep(10)  # Update every 10 seconds
                except Exception as e:
                    print(f"Health monitor error: {e}")
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def _update_system_metrics(self):
        """Update system-level metrics"""
        try:
            process = psutil.Process(os.getpid())
            with self.lock:
                self.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                self.cpu_percent = process.cpu_percent(interval=1)
        except Exception as e:
            print(f"Failed to update system metrics: {e}")
    
    def _cleanup_old_errors(self):
        """Remove errors older than 1 hour"""
        cutoff_time = time.time() - 3600
        with self.lock:
            self.errors_last_hour = [
                err for err in self.errors_last_hour 
                if err.get("timestamp", 0) > cutoff_time
            ]
    
    # ========================================================================
    # UPDATE METHODS
    # ========================================================================
    
    def update_websocket_status(self, connected: bool, reconnect: bool = False):
        """Update WebSocket connection status"""
        with self.lock:
            self.websocket_connected = connected
            if reconnect:
                self.reconnect_count += 1
    
    def record_tick(self):
        """Record WebSocket tick received"""
        with self.lock:
            self.last_tick_time = time.time()
            self.total_ticks_received += 1
    
    def update_data_status(self, symbols_tracked: int, candles_loaded: int,
                          missing_symbols: list):
        """Update data loading status"""
        with self.lock:
            self.symbols_tracked = symbols_tracked
            self.candles_loaded = candles_loaded
            self.missing_data_symbols = missing_symbols
    
    def record_scan_cycle(self, duration: float):
        """Record scan cycle completion"""
        with self.lock:
            self.last_scan_time = time.time()
            self.scan_cycle_times.append(duration)
            if len(self.scan_cycle_times) > 10:
                self.scan_cycle_times.pop(0)
    
    def record_error(self, severity: str, error_info: dict):
        """Record error occurrence"""
        with self.lock:
            error_info["timestamp"] = time.time()
            self.errors_last_hour.append(error_info)
            
            if severity == "critical":
                self.critical_errors += 1
            elif severity == "recoverable":
                self.recoverable_errors += 1
            elif severity == "warning":
                self.warnings += 1
    
    def record_pattern_detected(self):
        """Record pattern detection"""
        with self.lock:
            self.patterns_detected_today += 1
            self.last_pattern_time = time.time()
    
    def record_order_placed(self):
        """Record order placement"""
        with self.lock:
            self.orders_placed_today += 1
            self.last_order_time = time.time()
    
    def set_active_bots(self, count: int):
        """Set number of active bots"""
        with self.lock:
            self.active_bots = count
    
    # ========================================================================
    # STATUS METHODS
    # ========================================================================
    
    def get_overall_status(self) -> str:
        """
        Get overall health status
        Returns: "healthy" | "degraded" | "critical"
        """
        with self.lock:
            # Check critical conditions
            if self.critical_errors > 0:
                return "critical"
            
            if not self.websocket_connected and self.active_bots > 0:
                return "critical"
            
            # Check degraded conditions
            if self.reconnect_count > 5:
                return "degraded"
            
            if len(self.errors_last_hour) > 10:
                return "degraded"
            
            if self.memory_usage_mb > 1024:  # > 1GB
                return "degraded"
            
            if self.last_tick_time and (time.time() - self.last_tick_time) > 60:
                # No ticks for 1 minute while bot active
                if self.active_bots > 0:
                    return "degraded"
            
            return "healthy"
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        with self.lock:
            uptime = time.time() - self.start_time
            
            status = {
                "status": self.get_overall_status(),
                "uptime_seconds": int(uptime),
                "uptime_formatted": self._format_uptime(uptime),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                
                "websocket": {
                    "connected": self.websocket_connected,
                    "last_tick_seconds_ago": int(time.time() - self.last_tick_time) if self.last_tick_time else None,
                    "reconnect_count": self.reconnect_count,
                    "total_ticks": self.total_ticks_received
                },
                
                "data": {
                    "symbols_tracked": self.symbols_tracked,
                    "candles_loaded": self.candles_loaded,
                    "missing_data_count": len(self.missing_data_symbols),
                    "missing_symbols": self.missing_data_symbols[:5],  # First 5
                    "last_scan_seconds_ago": int(time.time() - self.last_scan_time) if self.last_scan_time else None
                },
                
                "errors": {
                    "last_hour": len(self.errors_last_hour),
                    "critical": self.critical_errors,
                    "recoverable": self.recoverable_errors,
                    "warnings": self.warnings,
                    "recent": self.errors_last_hour[-5:] if self.errors_last_hour else []
                },
                
                "performance": {
                    "scan_cycle_avg_seconds": round(sum(self.scan_cycle_times) / len(self.scan_cycle_times), 2) if self.scan_cycle_times else None,
                    "scan_cycle_last_seconds": round(self.scan_cycle_times[-1], 2) if self.scan_cycle_times else None,
                    "memory_mb": round(self.memory_usage_mb, 1),
                    "cpu_percent": round(self.cpu_percent, 1)
                },
                
                "trading": {
                    "active_bots": self.active_bots,
                    "patterns_detected_today": self.patterns_detected_today,
                    "orders_placed_today": self.orders_placed_today,
                    "last_pattern_seconds_ago": int(time.time() - self.last_pattern_time) if self.last_pattern_time else None,
                    "last_order_seconds_ago": int(time.time() - self.last_order_time) if self.last_order_time else None
                }
            }
            
            return status
    
    def get_simple_status(self) -> Dict[str, Any]:
        """Get simplified status for quick checks"""
        with self.lock:
            return {
                "status": self.get_overall_status(),
                "active_bots": self.active_bots,
                "websocket_connected": self.websocket_connected,
                "errors_last_hour": len(self.errors_last_hour),
                "memory_mb": round(self.memory_usage_mb, 1)
            }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def reset_daily_counters(self):
        """Reset daily counters (call at midnight)"""
        with self.lock:
            self.patterns_detected_today = 0
            self.orders_placed_today = 0
    
    def is_healthy(self) -> bool:
        """Quick health check"""
        return self.get_overall_status() == "healthy"


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get or create global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
