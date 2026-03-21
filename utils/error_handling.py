#!/usr/bin/env python3
"""
Enhanced error handling and resilience utilities
Provides retry mechanisms, circuit breaker pattern, and graceful error recovery
"""
import asyncio
import time
import functools
import requests
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
import logging
import traceback

class CircuitBreakerState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Circuit breaker is open, calls fail immediately
    HALF_OPEN = "half_open"  # Testing if service has recovered

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for external service calls
    Prevents cascade failures by temporarily disabling failing services
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")
                
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
            
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) >= self.recovery_timeout
        
    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class RetryConfig:
    """Configuration for retry mechanisms"""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, 
                 max_delay: float = 60.0, exponential_base: float = 2.0,
                 jitter: bool = True):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

def with_retry(config: RetryConfig, exceptions: tuple = (Exception,)):
    """
    Decorator for adding retry logic with exponential backoff
    
    Args:
        config: RetryConfig object with retry parameters
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        # Last attempt failed, re-raise exception
                        raise e
                        
                    # Calculate delay with exponential backoff
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random())
                        
                    logging.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    time.sleep(delay)
                    
            # Should never reach here
            raise last_exception
            
        return wrapper
    return decorator

async def with_async_retry(config: RetryConfig, exceptions: tuple = (Exception,)):
    """
    Async version of retry decorator
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        raise e
                        
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random())
                        
                    logging.warning(
                        f"Async attempt {attempt + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    await asyncio.sleep(delay)
                    
            raise last_exception
            
        return wrapper
    return decorator

class ResilientAPIClient:
    """
    Resilient API client with circuit breaker and retry mechanisms
    """
    
    def __init__(self, name: str = "APIClient", 
                 retry_config: Optional[RetryConfig] = None,
                 circuit_breaker_config: Optional[Dict] = None):
        self.name = name
        self.retry_config = retry_config or RetryConfig()
        
        cb_config = circuit_breaker_config or {}
        self.circuit_breaker = CircuitBreaker(**cb_config)
        
        self.session = requests.Session()
        self.session.timeout = 10
        
    def get(self, url: str, **kwargs) -> requests.Response:
        """Resilient GET request"""
        @with_retry(self.retry_config, (requests.RequestException,))
        def _make_request():
            return self.circuit_breaker.call(self.session.get, url, **kwargs)
            
        return _make_request()
        
    def post(self, url: str, **kwargs) -> requests.Response:
        """Resilient POST request"""
        @with_retry(self.retry_config, (requests.RequestException,))
        def _make_request():
            return self.circuit_breaker.call(self.session.post, url, **kwargs)
            
        return _make_request()

class ErrorTracker:
    """
    Track and analyze error patterns
    """
    
    def __init__(self, max_errors: int = 100):
        self.max_errors = max_errors
        self.errors: List[Dict] = []
        
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log error with context"""
        error_entry = {
            'timestamp': time.time(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.errors.append(error_entry)
        
        # Keep only recent errors
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
            
        logging.error(f"Error logged: {error_entry['error_type']}: {error_entry['error_message']}")
        
    def get_error_summary(self, time_window: int = 3600) -> Dict:
        """Get error summary for the last time_window seconds"""
        current_time = time.time()
        recent_errors = [
            e for e in self.errors 
            if current_time - e['timestamp'] <= time_window
        ]
        
        error_counts = {}
        for error in recent_errors:
            error_type = error['error_type']
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
        return {
            'total_errors': len(recent_errors),
            'error_types': error_counts,
            'time_window_hours': time_window / 3600
        }

def safe_execute(func: Callable, default_value: Any = None, 
                error_tracker: Optional[ErrorTracker] = None,
                context: Optional[Dict] = None) -> Any:
    """
    Safely execute a function and return default value on error
    """
    try:
        return func()
    except Exception as e:
        if error_tracker:
            error_tracker.log_error(e, context)
        else:
            logging.error(f"Error in safe_execute: {e}")
        return default_value

# Global instances for module-level usage
global_error_tracker = ErrorTracker()
waze_api_client = ResilientAPIClient(
    name="WazeAPI",
    retry_config=RetryConfig(max_attempts=3, base_delay=2.0),
    circuit_breaker_config={'failure_threshold': 3, 'recovery_timeout': 30}
)
telegram_api_client = ResilientAPIClient(
    name="TelegramAPI", 
    retry_config=RetryConfig(max_attempts=5, base_delay=1.0),
    circuit_breaker_config={'failure_threshold': 5, 'recovery_timeout': 60}
)

if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Test circuit breaker
    def failing_function():
        raise requests.ConnectionError("Service unavailable")
        
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5)
    
    for i in range(5):
        try:
            cb.call(failing_function)
        except Exception as e:
            print(f"Call {i+1}: {e}")
            print(f"Circuit breaker state: {cb.state}")