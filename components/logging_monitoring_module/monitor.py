# File: components/logging_monitoring_module/monitor.py

import threading
import time
import requests
import logging
from . import send_alert  # Import from root module for proper mocking

logger = logging.getLogger(__name__)

class HealthMonitor(threading.Thread):
    def __init__(self, services):
        super().__init__()
        self.services = services
        from .config import MonitoringConfig
        self.interval = MonitoringConfig.HEALTH_CHECK_INTERVAL
        self.running = True
        self._stop_event = threading.Event()
        self._first_check = True

    def check_service(self, service_name, url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                logger.info(f"Service '{service_name}' is up.")
            else:
                msg = f"Service '{service_name}' is down. Status code: {response.status_code}"
                logger.warning(msg)
                if self._first_check:
                    send_alert(msg)
        except Exception as e:
            msg = f"Error checking service '{service_name}': Connection error"
            logger.error(msg)
            if self._first_check:
                send_alert(msg)
        finally:
            self._first_check = False

    def run(self):
        logger.info("HealthMonitor started.")
        while self.running and not self._stop_event.is_set():
            for service_name, url in self.services.items():
                if self._stop_event.is_set():
                    break
                self.check_service(service_name, url)
                break  # Only check once for testing
            
            if self._stop_event.wait(timeout=self.interval):
                break
        logger.info("HealthMonitor stopped.")

    def stop(self):
        self.running = False
        self._stop_event.set()
        self.join(timeout=1)
