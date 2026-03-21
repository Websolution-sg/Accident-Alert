#!/usr/bin/env python3
"""
Enhanced testing framework with comprehensive test scenarios
Provides unit tests, integration tests, and end-to-end testing capabilities
"""
import unittest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import tempfile
import os
import requests_mock

# Import modules to test
from core.models import (
    Coordinates, Location, AccidentReport, AccidentSource, AccidentType,
    MessageStatus, WazeAccidentParser, TelegramAccidentParser
)
from core.api_clients import WazeAPIClient, TelegramAPIClient, TelegramUserClient
from utils.error_handling import CircuitBreaker, RetryConfig, with_retry, ResilientAPIClient
from utils.logging_utils import EnhancedLogger, PerformanceTracker, SystemHealthMonitor
from utils.config_manager import ConfigManager, AppConfig, Environment
from utils.performance_monitor import PerformanceMonitor, MetricCollector, APIMonitor

class TestCoordinates(unittest.TestCase):
    """Test coordinate handling and validation"""
    
    def test_valid_coordinates(self):
        """Test valid coordinate creation"""
        coords = Coordinates(1.3521, 103.8198)  # Singapore coordinates
        self.assertEqual(coords.latitude, 1.3521)
        self.assertEqual(coords.longitude, 103.8198)
    
    def test_invalid_latitude(self):
        """Test invalid latitude handling"""
        with self.assertRaises(ValueError):
            Coordinates(91.0, 103.8198)  # Invalid latitude > 90
        
        with self.assertRaises(ValueError):
            Coordinates(-91.0, 103.8198)  # Invalid latitude < -90
    
    def test_invalid_longitude(self):
        """Test invalid longitude handling"""
        with self.assertRaises(ValueError):
            Coordinates(1.3521, 181.0)  # Invalid longitude > 180
    
    def test_singapore_bounds_check(self):
        """Test Singapore bounds validation"""
        # Valid Singapore coordinates
        sg_coords = Coordinates(1.3521, 103.8198)
        self.assertTrue(sg_coords.is_within_singapore())
        
        # Outside Singapore
        non_sg_coords = Coordinates(2.0, 104.0)
        self.assertFalse(non_sg_coords.is_within_singapore())
    
    def test_distance_calculation(self):
        """Test distance calculation between coordinates"""
        coord1 = Coordinates(1.3521, 103.8198)  # Marina Bay
        coord2 = Coordinates(1.3644, 103.8227)  # Singapore Flyer
        
        distance = coord1.distance_to(coord2)
        
        # Distance should be approximately 1.4km
        self.assertAlmostEqual(distance, 1400, delta=200)  # Allow 200m margin

class TestAccidentParsers(unittest.TestCase):
    """Test accident data parsers"""
    
    def setUp(self):
        """Set up test parsers"""
        self.waze_parser = WazeAccidentParser()
        self.telegram_parser = TelegramAccidentParser()
    
    def test_waze_parser_valid_data(self):
        """Test Waze parser with valid accident data"""
        waze_data = {
            'type': 'ACCIDENT',
            'location': {'x': 103.8198, 'y': 1.3521},
            'street': 'Marina Bay Drive',
            'city': 'Singapore',
            'reportBy': 'TestUser',
            'confidence': 8,
            'reliability': 7,
            'pubMillis': int(time.time() * 1000)
        }
        
        self.assertTrue(self.waze_parser.can_parse(waze_data))
        
        accident = self.waze_parser.parse(waze_data)
        self.assertIsNotNone(accident)
        self.assertEqual(accident.source, AccidentSource.WAZE)
        self.assertEqual(accident.reported_by, 'TestUser')
        self.assertEqual(accident.confidence, 8)
        self.assertIsNotNone(accident.location.coordinates)
    
    def test_waze_parser_invalid_location(self):
        """Test Waze parser with coordinates outside Singapore"""
        waze_data = {
            'type': 'ACCIDENT',
            'location': {'x': 100.0, 'y': 5.0},  # Outside Singapore
            'street': 'Some Road',
            'city': 'Other City'
        }
        
        accident = self.waze_parser.parse(waze_data)
        self.assertIsNone(accident)  # Should be filtered out
    
    def test_telegram_parser_valid_message(self):
        """Test Telegram parser with valid accident message"""
        telegram_data = {
            'text': 'Accident on Orchard Road near Emerald Hill (1.3048, 103.8318)',
            'message_id': 12345,
            'date': int(time.time()),
            'chat': {'id': -1001486947378},
            'from': {'username': 'testuser'}
        }
        
        self.assertTrue(self.telegram_parser.can_parse(telegram_data))
        
        accident = self.telegram_parser.parse(telegram_data)
        self.assertIsNotNone(accident)
        self.assertEqual(accident.source, AccidentSource.TELEGRAM)
        self.assertIsNotNone(accident.location.coordinates)
        self.assertEqual(accident.original_message_id, 12345)
    
    def test_telegram_parser_malaysia_filter(self):
        """Test Telegram parser filters out Malaysia-specific messages"""
        telegram_data = {
            'text': 'Accident in Kuala Lumpur city center',
            'message_id': 12345,
            'date': int(time.time()),
            'chat': {'id': -1001486947378}
        }
        
        accident = self.telegram_parser.parse(telegram_data)
        self.assertIsNone(accident)  # Should be filtered out

class TestAPIClients(unittest.TestCase):
    """Test API client implementations"""
    
    def setUp(self):
        """Set up API clients for testing"""
        self.bbox = {
            'bottom': 1.1304753,
            'left': 103.6055424,
            'right': 104.0945619,
            'top': 1.4764671
        }
        
        self.waze_client = WazeAPIClient(
            "https://www.waze.com/live-map/api/georss",
            self.bbox
        )
        
        self.telegram_bot_client = TelegramAPIClient("test_bot_token")
    
    @requests_mock.Mocker()
    def test_waze_client_fetch_alerts(self, m):
        """Test Waze client alert fetching"""
        # Mock Waze API response
        mock_response = {
            'alerts': [
                {
                    'type': 'ACCIDENT',
                    'location': {'x': 103.8198, 'y': 1.3521},
                    'street': 'Test Street',
                    'city': 'Singapore',
                    'reportBy': 'TestUser',
                    'confidence': 8,
                    'pubMillis': int(time.time() * 1000)
                },
                {
                    'type': 'TRAFFIC_JAM',
                    'location': {'x': 103.8300, 'y': 1.3600},
                    'street': 'Other Street'
                }
            ]
        }
        
        m.get(requests_mock.ANY, json=mock_response)
        
        alerts = self.waze_client.fetch_raw_alerts()
        self.assertEqual(len(alerts), 2)
        
        accidents = self.waze_client.fetch_accidents()
        self.assertEqual(len(accidents), 1)  # Only one accident type
        self.assertEqual(accidents[0].source, AccidentSource.WAZE)
    
    @requests_mock.Mocker()
    def test_telegram_bot_send_message(self, m):
        """Test Telegram bot message sending"""
        mock_response = {
            'ok': True,
            'result': {
                'message_id': 123,
                'date': int(time.time()),
                'text': 'Test message',
                'chat': {'id': -1003683261194}
            }
        }
        
        m.post(requests_mock.ANY, json=mock_response)
        
        result = self.telegram_bot_client.send_message(
            "-1003683261194",
            "Test accident message"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['message_id'], 123)
    
    @requests_mock.Mocker()
    def test_telegram_bot_health_check(self, m):
        """Test Telegram bot health check"""
        mock_response = {
            'ok': True,
            'result': {
                'id': 123456789,
                'is_bot': True,
                'first_name': 'TestBot',
                'username': 'test_bot'
            }
        }
        
        m.get(requests_mock.ANY, json=mock_response)
        
        health = self.telegram_bot_client.health_check()
        
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['bot_username'], 'test_bot')

class TestErrorHandling(unittest.TestCase):
    """Test error handling and resilience utilities"""
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        def failing_function():
            raise Exception("Service unavailable")
        
        # First failure
        with self.assertRaises(Exception):
            cb.call(failing_function)
        self.assertEqual(cb.failure_count, 1)
        
        # Second failure - should open circuit
        with self.assertRaises(Exception):
            cb.call(failing_function)
        self.assertEqual(cb.failure_count, 2)
        self.assertTrue(cb.state.name == 'OPEN')
        
        # Third call should fail immediately due to open circuit
        with self.assertRaises(Exception) as context:
            cb.call(failing_function)
        self.assertIn("Circuit breaker is OPEN", str(context.exception))
    
    def test_retry_decorator(self):
        """Test retry decorator with exponential backoff"""
        config = RetryConfig(max_attempts=3, base_delay=0.1)
        
        self.call_count = 0
        
        @with_retry(config, (ValueError,))
        def sometimes_failing_function():
            self.call_count += 1
            if self.call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = sometimes_failing_function()
        self.assertEqual(result, "success")
        self.assertEqual(self.call_count, 3)

class TestLoggingUtils(unittest.TestCase):
    """Test logging utilities"""
    
    def test_enhanced_logger_context(self):
        """Test enhanced logger with context management"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")
            logger = EnhancedLogger("test", log_file, json_format=True)
            
            with logger.operation_context("test_operation"):
                logger.info("Test message")
            
            # Verify log file was created
            self.assertTrue(os.path.exists(log_file))
            
            # Check metrics were collected
            if logger.performance:
                summary = logger.get_metrics_summary()
                self.assertIn('counters', summary)
    
    def test_performance_tracker(self):
        """Test performance tracking"""
        tracker = PerformanceTracker()
        
        # Test timing
        with tracker.timer("test_operation"):
            time.sleep(0.1)  # Simulate work
        
        # Test counter
        tracker.increment_counter("test_counter", tags={'env': 'test'})
        tracker.increment_counter("test_counter", tags={'env': 'test'})
        
        summary = tracker.get_summary()
        self.assertIn('timing_stats', summary)
        self.assertIn('test_operation', summary['timing_stats'])
        self.assertIn('counters', summary)

class TestConfigManager(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test configuration"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Test valid config
        config = AppConfig()
        config.telegram.bot_token = "valid_token"
        config.telegram.api_id = 12345
        config.telegram.api_hash = "valid_hash"
        config.telegram.phone_number = "+1234567890"
        
        errors = self.config_manager._validate_config(config)
        self.assertEqual(len(errors), 0)
        
        # Test invalid config
        invalid_config = AppConfig()
        errors = self.config_manager._validate_config(invalid_config)
        self.assertGreater(len(errors), 0)
    
    def test_config_save_load(self):
        """Test saving and loading configuration"""
        config = AppConfig()
        config.environment = Environment.PRODUCTION
        config.telegram.bot_token = "test_token"
        config.telegram.api_id = 12345
        config.telegram.api_hash = "test_hash"
        config.telegram.phone_number = "+1234567890"
        
        # Save config
        self.config_manager.save_to_file(config, "test_config.yaml")
        
        # Load config
        loaded_config = self.config_manager.load_from_file("test_config.yaml")
        
        self.assertEqual(loaded_config.environment, Environment.PRODUCTION)
        self.assertEqual(loaded_config.telegram.bot_token, "test_token")

class TestPerformanceMonitor(unittest.TestCase):
    """Test performance monitoring system"""
    
    def setUp(self):
        """Set up performance monitor"""
        self.monitor = PerformanceMonitor()
    
    def test_metric_collection(self):
        """Test metric collection"""
        # Record some metrics
        self.monitor.collector.increment_counter("test_counter")
        self.monitor.collector.set_gauge("test_gauge", 42.0)
        
        # Verify metrics were recorded
        counter_value = self.monitor.collector.get_counter_value("test_counter")
        self.assertEqual(counter_value, 1)
        
        gauge_value = self.monitor.collector.get_gauge("test_gauge")
        self.assertEqual(gauge_value, 42.0)
    
    def test_api_monitoring(self):
        """Test API performance monitoring"""
        # Simulate successful API call
        with self.monitor.api_monitor.monitor_request("test_api"):
            time.sleep(0.05)  # Simulate work
        
        # Check health status
        health = self.monitor.api_monitor.get_api_health("test_api")
        self.assertIn('status', health)
        self.assertGreater(health['success_rate'], 0)
    
    def test_dashboard_data(self):
        """Test dashboard data generation"""
        # Generate some activity
        with self.monitor.api_monitor.monitor_request("test_api"):
            pass
            
        dashboard = self.monitor.get_dashboard_data()
        
        self.assertIn('timestamp', dashboard)
        self.assertIn('api_health', dashboard)
        self.assertIn('recent_alerts', dashboard)

class IntegrationTests(unittest.TestCase):
    """Integration tests for complete workflows"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @requests_mock.Mocker()
    def test_end_to_end_waze_processing(self, m):
        """Test complete Waze accident processing pipeline"""
        # Mock Waze API
        mock_waze_response = {
            'alerts': [{
                'type': 'ACCIDENT',
                'location': {'x': 103.8198, 'y': 1.3521},
                'street': 'Marina Bay Drive',
                'city': 'Singapore',
                'reportBy': 'TestUser',
                'confidence': 8,
                'pubMillis': int(time.time() * 1000)
            }]
        }
        m.get(requests_mock.ANY, json=mock_waze_response)
        
        # Mock Telegram API
        mock_telegram_response = {
            'ok': True,
            'result': {'message_id': 123}
        }
        m.post(requests_mock.ANY, json=mock_telegram_response)
        
        # Create clients
        bbox = {
            'bottom': 1.1304753, 'left': 103.6055424,
            'right': 104.0945619, 'top': 1.4764671
        }
        
        waze_client = WazeAPIClient("https://www.waze.com/live-map/api/georss", bbox)
        telegram_client = TelegramAPIClient("test_token")
        
        # Process workflow
        accidents = waze_client.fetch_accidents()
        self.assertEqual(len(accidents), 1)
        
        # Send message
        message = accidents[0].to_telegram_message()
        result = telegram_client.send_message("-1003683261194", message)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['message_id'], 123)

def create_test_suite() -> unittest.TestSuite:
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCoordinates,
        TestAccidentParsers,
        TestAPIClients,
        TestErrorHandling,
        TestLoggingUtils,
        TestConfigManager,
        TestPerformanceMonitor,
        IntegrationTests
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def run_tests(verbosity: int = 2) -> unittest.TestResult:
    """Run all tests with specified verbosity"""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)

if __name__ == "__main__":
    # Run all tests
    print("Running enhanced test suite...")
    print("=" * 60)
    
    start_time = time.time()
    result = run_tests(verbosity=2)
    duration = time.time() - start_time
    
    print("=" * 60)
    print(f"Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Duration: {duration:.2f} seconds")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    exit(0 if success else 1)