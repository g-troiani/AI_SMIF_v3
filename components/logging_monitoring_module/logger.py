# File: components/logging_monitoring_module/logger.py

import logging
from .logging_config import setup_logging

def get_logger(name):
    setup_logging()
    return logging.getLogger(name)