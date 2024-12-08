# File: components/logging_monitoring_module/logging_config.py

import logging
import logging.config
from .config import LoggingConfig

def setup_logging():
    LoggingConfig.ensure_log_directory()
    
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': LoggingConfig.LOG_LEVEL,
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'file': {
                'level': 'WARNING',
                'class': 'logging.FileHandler',
                'filename': LoggingConfig.LOG_FILE,
                'formatter': 'standard',
                'encoding': 'utf8'
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': LoggingConfig.LOG_LEVEL,
                'propagate': True
            },
        }
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)
