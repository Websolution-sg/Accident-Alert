#!/usr/bin/env python3
"""
Enhanced structured logging system with metrics and monitoring
Provides centralized logging, performance metrics, and health monitoring
"""
import logging
import logging.handlers
import json
import time
import datetime
import os
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
import threading
from contextlib import contextmanager

@dataclass
class LogContext:
    """Structured context for logging"""
    component: str = "unknown"
    operation: str = "unknown" 
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class MetricEvent:
    """Performance metric event"""
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logs
    """
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_obj['context'] = asdict(record.context)
            
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in log_obj and not key.startswith('_'):
                log_obj[key] = value
                
        return json.dumps(log_obj, default=str)

class PerformanceTracker:
    """
    Track performance metrics and timing information
    """
    
    def __init__(self):
        self.metrics: deque = deque(maxlen=1000)  # Keep last 1000 metrics
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        
    def record_metric(self, event: MetricEvent):
        """Record a metric event"""
        with self._lock:
            self.metrics.append(event)
            
    def increment_counter(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = f"{name}:{json.dumps(tags or {}, sort_keys=True)}"
        with self._lock:
            self.counters[key] += 1
            
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timing metric"""
        self.record_metric(MetricEvent(
            name=name,
            value=duration, 
            unit="seconds",
            tags=tags or {}
        ))
        
        with self._lock:
            self.timers[name].append(duration)
            # Keep only recent measurements
            if len(self.timers[name]) > 100:
                self.timers[name] = self.timers[name][-100:]
                
    @contextmanager
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timing(name, duration, tags)
            
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self._lock:
            summary = {
                'counters': dict(self.counters),
                'recent_metrics_count': len(self.metrics),
                'timing_stats': {}
            }
            
            # Calculate timing statistics
            for name, times in self.timers.items():
                if times:
                    summary['timing_stats'][name] = {
                        'count': len(times),
                        'avg': sum(times) / len(times),
                        'min': min(times),
                        'max': max(times)
                    }
                    
        return summary

class EnhancedLogger:
    """
    Enhanced logger with structured logging and metrics
    """
    
    def __init__(self, name: str, log_file: Optional[str] = None, 
                 json_format: bool = True, performance_tracking: bool = True):
        self.name = name
        self.logger = logging.getLogger(name)
        self.context: Optional[LogContext] = None
        
        if performance_tracking:
            self.performance = PerformanceTracker()
        else:
            self.performance = None
            
        self._setup_handlers(log_file, json_format)
        
    def _setup_handlers(self, log_file: Optional[str], json_format: bool):
        """Setup logging handlers"""
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # File handler (with rotation)
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB per file, 5 backups
            )
            file_handler.setLevel(logging.DEBUG)
        
        # Set formatters
        if json_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
        console_handler.setFormatter(formatter)
        if log_file:
            file_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        if log_file:
            self.logger.addHandler(file_handler)
            
    def set_context(self, context: LogContext):
        """Set logging context"""
        self.context = context
        
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context"""
        extra = kwargs.copy()
        if self.context:
            extra['context'] = self.context
            
        self.logger.log(level, message, extra=extra)
        
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, **kwargs)
        if self.performance:
            self.performance.increment_counter('log.info')
        
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)
        if self.performance:
            self.performance.increment_counter('log.warning')
        
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message"""
        if error:
            kwargs['exc_info'] = (type(error), error, error.__traceback__)
        self._log_with_context(logging.ERROR, message, **kwargs)
        if self.performance:
            self.performance.increment_counter('log.error')
            
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
        if self.performance:
            self.performance.increment_counter('log.critical')
            
    @contextmanager
    def operation_context(self, operation: str, **context_kwargs):
        """Context manager for operation-level logging"""
        old_context = self.context
        operation_context = LogContext(
            component=self.name,
            operation=operation,
            **context_kwargs
        )
        
        self.set_context(operation_context)
        start_time = time.time()
        
        try:
            self.info(f"Starting operation: {operation}")
            yield self
            duration = time.time() - start_time
            self.info(f"Completed operation: {operation} in {duration:.3f}s")
            
            if self.performance:
                self.performance.record_timing(f"operation.{operation}", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.error(f"Failed operation: {operation} after {duration:.3f}s", error=e)
            raise
        finally:
            self.set_context(old_context)
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        if not self.performance:
            return {}
        return self.performance.get_summary()

class SystemHealthMonitor:
    """
    Monitor system health and resource usage
    """
    
    def __init__(self, logger: EnhancedLogger):
        self.logger = logger
        self.health_data = deque(maxlen=100)  # Last 100 health checks
        
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total_mb': memory.total // (1024*1024),
                'available_mb': memory.available // (1024*1024), 
                'percent': memory.percent
            }
        except ImportError:
            return {'error': 'psutil not available'}
            
    def check_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """Check disk usage"""
        try:
            import psutil
            disk = psutil.disk_usage(path)
            return {
                'total_gb': disk.total // (1024*1024*1024),
                'used_gb': disk.used // (1024*1024*1024),
                'free_gb': disk.free // (1024*1024*1024),
                'percent': (disk.used / disk.total) * 100
            }
        except ImportError:
            return {'error': 'psutil not available'}
            
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'memory': self.check_memory_usage(),
            'disk': self.check_disk_usage(),
            'logger_metrics': self.logger.get_metrics_summary()
        }
        
        self.health_data.append(health_data)
        return health_data
        
    def log_health_status(self):
        """Log current health status"""
        health = self.health_check()
        
        memory_warning = False
        disk_warning = False
        
        if 'percent' in health['memory'] and health['memory']['percent'] > 80:
            memory_warning = True
            
        if 'percent' in health['disk'] and health['disk']['percent'] > 80:
            disk_warning = True
            
        if memory_warning or disk_warning:
            self.logger.warning(f"Resource usage high", health_data=health)
        else:
            self.logger.info(f"System health check", health_data=health)

# Factory function for creating loggers
def create_logger(component: str, log_dir: str = "logs", 
                 json_format: bool = True) -> EnhancedLogger:
    """Create configured logger for component"""
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{component}.log")
    logger = EnhancedLogger(component, log_file, json_format)
    
    return logger

# Default loggers for the application
waze_logger = create_logger("waze_monitor")
telegram_logger = create_logger("telegram_monitor") 
system_logger = create_logger("system")
api_logger = create_logger("api_client")

# System health monitor
health_monitor = SystemHealthMonitor(system_logger)

if __name__ == "__main__":
    # Example usage
    logger = create_logger("test")
    
    # Set context
    logger.set_context(LogContext(
        component="test", 
        operation="demo",
        session_id="test-123"
    ))
    
    # Test different log levels
    logger.info("Test info message")
    logger.warning("Test warning message")
    
    # Test operation context
    with logger.operation_context("data_processing"):
        logger.info("Processing data...")
        time.sleep(0.1)  # Simulate work
        
    # Test metrics
    print(json.dumps(logger.get_metrics_summary(), indent=2))