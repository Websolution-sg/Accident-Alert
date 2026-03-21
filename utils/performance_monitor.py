#!/usr/bin/env python3
"""
Performance monitoring and alerting utilities
Provides system monitoring, API performance tracking, and alerting mechanisms
"""
import time
import datetime
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, NamedTuple
from dataclasses import dataclass, field
from collections import deque, defaultdict
from contextlib import contextmanager
import threading
import statistics
import requests
from enum import Enum

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    timestamp: float
    unit: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
@dataclass 
class Alert:
    """System alert"""
    level: AlertLevel
    message: str
    timestamp: float
    component: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class MetricCollector:
    """
    Collect and analyze performance metrics
    """
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self._lock = threading.Lock()
        
    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        with self._lock:
            self.metrics.append(metric)
            
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        key = self._make_key(name, tags)
        with self._lock:
            self.counters[key] += value
            
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        key = self._make_key(name, tags)
        with self._lock:
            self.gauges[key] = value
            
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get current gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key)
        
    def _make_key(self, name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create metric key with tags"""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}:{tag_str}"
        return name
        
    def get_counter_value(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)
        
    def get_metrics_by_name(self, name: str, time_window: Optional[float] = None) -> List[PerformanceMetric]:
        """Get metrics by name within time window"""
        now = time.time()
        cutoff = now - time_window if time_window else 0
        
        with self._lock:
            return [
                m for m in self.metrics 
                if m.name == name and m.timestamp >= cutoff
            ]
            
    def calculate_statistics(self, name: str, time_window: float = 3600) -> Dict[str, Any]:
        """Calculate statistics for a metric"""
        metrics = self.get_metrics_by_name(name, time_window)
        
        if not metrics:
            return {}
            
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'p95': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
            'p99': statistics.quantiles(values, n=100)[98] if len(values) >= 100 else max(values)
        }

class APIMonitor:
    """
    Monitor API performance and health
    """
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
    @contextmanager
    def monitor_request(self, api_name: str, endpoint: str = ""):
        """Context manager to monitor API request performance"""
        start_time = time.time()
        tags = {'api': api_name, 'endpoint': endpoint}
        
        try:
            yield
            
            # Success case  
            duration = time.time() - start_time
            self.collector.record_metric(PerformanceMetric(
                name="api.response_time",
                value=duration,
                timestamp=time.time(),
                unit="seconds",
                tags=tags
            ))
            
            self.collector.increment_counter("api.requests.success", tags=tags)
            self.response_times[api_name].append(duration)
            
        except Exception as e:
            # Error case
            duration = time.time() - start_time
            error_tags = {**tags, 'error_type': type(e).__name__}
            
            self.collector.increment_counter("api.requests.error", tags=error_tags)
            self.collector.record_metric(PerformanceMetric(
                name="api.error_response_time",
                value=duration, 
                timestamp=time.time(),
                unit="seconds",
                tags=error_tags
            ))
            raise
            
    def get_api_health(self, api_name: str) -> Dict[str, Any]:
        """Get health status for an API"""
        recent_times = list(self.response_times[api_name])
        
        if not recent_times:
            return {'status': 'no_data', 'message': 'No recent requests'}
            
        avg_time = sum(recent_times) / len(recent_times)
        success_count = self.collector.get_counter_value("api.requests.success", {'api': api_name})
        error_count = self.collector.get_counter_value("api.requests.error", {'api': api_name})
        
        total_requests = success_count + error_count
        success_rate = success_count / total_requests if total_requests > 0 else 0
        
        # Determine health status
        if success_rate < 0.5:
            status = 'critical'
        elif success_rate < 0.8 or avg_time > 10.0:
            status = 'warning'
        else:
            status = 'healthy'
            
        return {
            'status': status,
            'success_rate': success_rate,
            'avg_response_time': avg_time,
            'total_requests': total_requests,
            'success_count': success_count,
            'error_count': error_count
        }

class SystemResourceMonitor:
    """
    Monitor system resources (memory, CPU, disk)
    """
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
        
    def collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            import psutil
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.collector.set_gauge("system.memory.percent", memory.percent)
            self.collector.set_gauge("system.memory.available_mb", memory.available / (1024*1024))
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.collector.set_gauge("system.cpu.percent", cpu_percent)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.collector.set_gauge("system.disk.percent", (disk.used / disk.total) * 100)
            self.collector.set_gauge("system.disk.free_gb", disk.free / (1024*1024*1024))
            
        except ImportError:
            # psutil not available, collect basic info
            pass
            
    def get_resource_status(self) -> Dict[str, Any]:
        """Get current resource status"""
        return {
            'memory_percent': self.collector.get_gauge("system.memory.percent"),
            'cpu_percent': self.collector.get_gauge("system.cpu.percent"),
            'disk_percent': self.collector.get_gauge("system.disk.percent"),
            'disk_free_gb': self.collector.get_gauge("system.disk.free_gb")
        }

class AlertManager: 
    """
    Manage system alerts and notifications
    """
    
    def __init__(self, bot_token: str = None, alert_channel: str = None):
        self.bot_token = bot_token
        self.alert_channel = alert_channel
        self.alerts: deque = deque(maxlen=500)  # Keep last 500 alerts
        self.alert_rules: List[Callable] = []
        self.last_alert_times: Dict[str, float] = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts
        
    def add_alert_rule(self, rule: Callable[[MetricCollector], Optional[Alert]]):
        """Add an alert rule function"""
        self.alert_rules.append(rule)
        
    def check_alerts(self, collector: MetricCollector) -> List[Alert]:
        """Check all alert rules and generate alerts"""
        new_alerts = []
        
        for rule in self.alert_rules:
            try:
                alert = rule(collector)
                if alert and self._should_send_alert(alert):
                    new_alerts.append(alert)
                    self.alerts.append(alert)
                    self._update_alert_time(alert)
                    
            except Exception as e:
                # Error in alert rule itself
                error_alert = Alert(
                    level=AlertLevel.ERROR,
                    message=f"Alert rule error: {e}",
                    timestamp=time.time(),
                    component="alerting",
                    metadata={'rule_error': str(e)}
                )
                new_alerts.append(error_alert)
                
        return new_alerts
        
    def _should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent (respects cooldown)"""
        alert_key = f"{alert.component}:{alert.metric_name}:{alert.level.value}"
        last_time = self.last_alert_times.get(alert_key, 0)
        
        return (time.time() - last_time) >= self.alert_cooldown
        
    def _update_alert_time(self, alert: Alert):
        """Update last alert time for cooldown tracking"""
        alert_key = f"{alert.component}:{alert.metric_name}:{alert.level.value}"
        self.last_alert_times[alert_key] = time.time()
        
    async def send_telegram_alert(self, alert: Alert):
        """Send alert via Telegram"""
        if not self.bot_token or not self.alert_channel:
            return
            
        icon_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️", 
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        icon = icon_map.get(alert.level, "🔍")
        timestamp = datetime.datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"{icon} **{alert.level.value.upper()} Alert**\n\n"
        message += f"**Component:** {alert.component}\n"
        message += f"**Message:** {alert.message}\n"
        message += f"**Time:** {timestamp}\n"
        
        if alert.metric_name:
            message += f"**Metric:** {alert.metric_name}\n"
        if alert.metric_value is not None:
            message += f"**Value:** {alert.metric_value}\n"
        if alert.threshold is not None:
            message += f"**Threshold:** {alert.threshold}\n"
            
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                'chat_id': self.alert_channel,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            async with requests.Session() as session:
                response = await session.post(url, json=payload, timeout=10)
                response.raise_for_status()
                
        except Exception as e:
            # Failed to send alert - log it
            print(f"Failed to send Telegram alert: {e}")

class PerformanceMonitor:
    """
    Main performance monitoring orchestrator
    """
    
    def __init__(self, bot_token: str = None, alert_channel: str = None):
        self.collector = MetricCollector()
        self.api_monitor = APIMonitor(self.collector)
        self.resource_monitor = SystemResourceMonitor(self.collector)
        self.alert_manager = AlertManager(bot_token, alert_channel)
        
        self.is_running = False
        self.monitor_thread = None
        
        # Add default alert rules
        self._setup_default_alerts()
        
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        
        def memory_alert_rule(collector: MetricCollector) -> Optional[Alert]:
            memory_percent = collector.get_gauge("system.memory.percent")
            if memory_percent and memory_percent > 85:
                return Alert(
                    level=AlertLevel.WARNING,
                    message=f"High memory usage: {memory_percent:.1f}%",
                    timestamp=time.time(),
                    component="system",
                    metric_name="memory_percent",
                    metric_value=memory_percent,
                    threshold=85.0
                )
            return None
            
        def api_error_rate_rule(collector: MetricCollector) -> Optional[Alert]:
            api_names = ['waze', 'telegram'] 
            for api_name in api_names:
                health = self.api_monitor.get_api_health(api_name)
                if health.get('success_rate', 1.0) < 0.5 and health.get('total_requests', 0) > 10:
                    return Alert(
                        level=AlertLevel.ERROR,
                        message=f"{api_name} API has low success rate: {health['success_rate']:.1%}",
                        timestamp=time.time(),
                        component=api_name,
                        metric_name="success_rate", 
                        metric_value=health['success_rate'],
                        threshold=0.5
                    )
            return None
            
        self.alert_manager.add_alert_rule(memory_alert_rule)
        self.alert_manager.add_alert_rule(api_error_rate_rule)
        
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring"""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                self.resource_monitor.collect_system_metrics()
                
                # Check for alerts
                alerts = self.alert_manager.check_alerts(self.collector)
                
                # Send alerts (in a non-blocking way)
                for alert in alerts:
                    asyncio.create_task(self.alert_manager.send_telegram_alert(alert))
                    
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)
                
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for monitoring UI"""
        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'system_resources': self.resource_monitor.get_resource_status(), 
            'api_health': {
                'waze': self.api_monitor.get_api_health('waze'),
                'telegram': self.api_monitor.get_api_health('telegram')
            },
            'recent_alerts': [
                {
                    'level': alert.level.value,
                    'message': alert.message,
                    'component': alert.component,
                    'timestamp': datetime.datetime.fromtimestamp(alert.timestamp).isoformat()
                }
                for alert in list(self.alert_manager.alerts)[-10:]  # Last 10 alerts
            ],
            'total_metrics': len(self.collector.metrics)
        }

# Global performance monitor for easy access
performance_monitor = PerformanceMonitor()

if __name__ == "__main__":
    # Example usage
    monitor = PerformanceMonitor()
    
    # Start monitoring
    monitor.start_monitoring(interval=30)
    
    # Simulate some API calls
    with monitor.api_monitor.monitor_request("waze", "/api/alerts"):
        time.sleep(0.5)  # Simulate API call
        
    with monitor.api_monitor.monitor_request("telegram", "/sendMessage"):
        time.sleep(0.2)
        
    # Get dashboard data
    dashboard = monitor.get_dashboard_data()
    print(json.dumps(dashboard, indent=2))
    
    # Stop monitoring
    time.sleep(2)
    monitor.stop_monitoring()