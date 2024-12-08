# File: components/logging_monitoring_module/__init__.py

# Import core components for top-level access and mocking
from .alerts import send_alert
from .config import LoggingConfig, MonitoringConfig
from .logger import get_logger
from .monitor import HealthMonitor