# File: components/trading_execution_engine/config.py
# Type: py

import os
from configparser import ConfigParser

# Create directories if they don't exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Initialize ConfigParser
config_parser = ConfigParser()

# Load configuration from file if it exists
config_file_path = os.path.join('config', 'config.ini')
if os.path.exists(config_file_path):
    config_parser.read(config_file_path)
else:
    print(f"Configuration file not found at {config_file_path}. Using environment variables.")

# Alpaca API Settings
APCA_API_BASE_URL = os.getenv('APCA_API_BASE_URL') or config_parser.get('alpaca', 'base_url', fallback='https://paper-api.alpaca.markets/v2')
APCA_API_KEY_ID = os.getenv('APCA_API_KEY_ID') or config_parser.get('alpaca', 'key_id', fallback=None)
APCA_API_SECRET_KEY = os.getenv('APCA_API_SECRET_KEY') or config_parser.get('alpaca', 'secret_key', fallback=None)

if not APCA_API_KEY_ID or not APCA_API_SECRET_KEY:
    raise EnvironmentError("Alpaca API credentials not found. Please set environment variables or update the config file.")

# Risk Management Settings
MAX_POSITION_SIZE_PCT = float(os.getenv('MAX_POSITION_SIZE_PCT') or config_parser.get('risk', 'max_position_size_pct', fallback=0.1))
MAX_ORDER_VALUE = float(os.getenv('MAX_ORDER_VALUE') or config_parser.get('risk', 'max_order_value', fallback=50000.0))
DAILY_LOSS_LIMIT_PCT = float(os.getenv('DAILY_LOSS_LIMIT_PCT') or config_parser.get('risk', 'daily_loss_limit_pct', fallback=0.02))

# Logging Settings
LOG_FILE = os.path.join('logs', 'execution_engine.log')

# Configuration Dictionary
CONFIG = {
    'alpaca': {
        'base_url': APCA_API_BASE_URL,
        'key_id': APCA_API_KEY_ID,
        'secret_key': APCA_API_SECRET_KEY
    },
    'logging': {
        'log_file': LOG_FILE
    },
    'database': {
        'orders_db': os.path.join('data', 'orders.db')
    },
    'risk': {
        'max_position_size_pct': MAX_POSITION_SIZE_PCT,
        'max_order_value': MAX_ORDER_VALUE,
        'daily_loss_limit_pct': DAILY_LOSS_LIMIT_PCT
    }
}

# Make config available for import
__all__ = ['CONFIG']
