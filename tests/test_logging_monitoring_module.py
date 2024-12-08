import unittest
import os
import logging
import threading
import time
from unittest.mock import patch, MagicMock

# Assuming the logging_monitoring_module is in the components directory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from components.logging_monitoring_module.logger import get_logger
from components.logging_monitoring_module.monitor import HealthMonitor
from components.logging_monitoring_module.alerts import send_alert
from components.logging_monitoring_module.config import MonitoringConfig, LoggingConfig
from components.logging_monitoring_module.logging_config import setup_logging

class TestLoggingAndMonitoringModule(unittest.TestCase):
    def setUp(self):
        """
        Set up test environment with proper logging configuration
        """
        # Set up test directory in current test directory
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Set up log file
        self.log_file = os.path.join(self.test_dir, 'test.log')
        
        # Configure logging
        LoggingConfig.LOG_FILE = self.log_file
        LoggingConfig._initialized = False
        
        # Initialize logger after setting up configuration
        setup_logging()
        self.logger = get_logger(__name__)

    def test_logger_configuration(self):
        """
        Test basic logging functionality
        """
        # Write test messages
        self.logger.warning("Test warning message")
        self.logger.error("Test error message")
        
        # Ensure file operations complete
        time.sleep(0.2)
        
        # Debug print for troubleshooting
        print(f"Looking for log file at: {self.log_file}")
        print(f"Directory contents: {os.listdir(self.test_dir)}")
        
        # Verify log file creation
        self.assertTrue(os.path.exists(self.log_file), "Log file was not created")
        
        # Verify log contents
        with open(self.log_file, 'r') as f:
            log_contents = f.read()
            self.assertIn("Test warning message", log_contents)
            self.assertIn("Test error message", log_contents)

    def test_get_logger(self):
        """
        Test logger instantiation
        """
        logger = get_logger('test_logger')
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, 'test_logger')

    @patch('components.logging_monitoring_module.monitor.send_alert')
    @patch('requests.get')
    def test_health_monitor_service_up(self, mock_get, mock_send_alert):
        """
        Test health monitor with healthy service
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        monitor = HealthMonitor({'TestService': 'http://test/health'})
        monitor.interval = 0.5
        
        try:
            monitor.start()
            time.sleep(0.6)
        finally:
            monitor.stop()
            monitor.join(timeout=1)

        mock_send_alert.assert_not_called()

    @patch('components.logging_monitoring_module.monitor.send_alert')
    @patch('requests.get')
    def test_health_monitor_service_down(self, mock_get, mock_send_alert):
        """
        Test health monitor with failing service
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        monitor = HealthMonitor({'TestService': 'http://test/health'})
        monitor.interval = 0.5
        
        try:
            monitor.start()
            time.sleep(0.6)
        finally:
            monitor.stop()
            monitor.join(timeout=1)

        mock_send_alert.assert_called_once_with(
            "Service 'TestService' is down. Status code: 500"
        )

    @patch('components.logging_monitoring_module.monitor.send_alert')
    @patch('requests.get')
    def test_health_monitor_exception(self, mock_get, mock_send_alert):
        """
        Test health monitor with connection error
        """
        mock_get.side_effect = Exception("Connection error")

        monitor = HealthMonitor({'TestService': 'http://test/health'})
        monitor.interval = 0.5
        
        try:
            monitor.start()
            time.sleep(0.6)
        finally:
            monitor.stop()
            monitor.join(timeout=1)

        mock_send_alert.assert_called_once_with(
            "Error checking service 'TestService': Connection error"
        )

    def test_send_alert(self):
        """
        Test alert sending functionality
        """
        with patch('components.logging_monitoring_module.config.MonitoringConfig.ALERT_RECIPIENTS', ['devops@example.com']):
            with patch('logging.Logger.warning') as mock_warning:
                message = "Test alert message"
                send_alert(message)
                mock_warning.assert_called_with(
                    f"Alert sent to devops@example.com: {message}"
                )

    def tearDown(self):
        """
        Clean up test resources
        """
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            if os.path.exists(self.test_dir):
                os.rmdir(self.test_dir)
        except (PermissionError, OSError) as e:
            print(f"Cleanup failed: {e}")

if __name__ == '__main__':
    unittest.main()