# File: components/logging_monitoring_module/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class LoggingConfig:
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/application.log')
    _initialized = False

    @classmethod
    def ensure_log_directory(cls):
        if not cls._initialized:
            path = Path(cls.LOG_FILE).resolve()  # Get absolute path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(exist_ok=True)
            cls._initialized = True

class MonitoringConfig:
    ENABLE_MONITORING = os.getenv('ENABLE_MONITORING', 'True') == 'True'
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', '60'))
    ALERT_RECIPIENTS = os.getenv('ALERT_RECIPIENTS', 'admin@example.com').split(',')