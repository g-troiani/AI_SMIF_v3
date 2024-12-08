# File: components/logging_monitoring_module/alerts.py

import logging

logger = logging.getLogger(__name__)

def send_alert(message):
    from .config import MonitoringConfig
    recipients = MonitoringConfig.ALERT_RECIPIENTS
    for recipient in recipients:
        logger.warning(f"Alert sent to {recipient}: {message}")