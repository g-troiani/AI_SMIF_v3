# File: components/data_management_module/config.py
# 
# Unified configuration file combining both the original data_management_module/config.py 
# and the trading_execution_engine/config.py into a single module.
# 
# This single config.py now provides:
#   1) The DataConfig class for data & environment-based settings (database paths, logging, etc.).
#   2) The additional Alpaca, risk, and logging configuration previously in the trading_execution_engine.
#   3) The UnifiedConfigLoader class for backtest/live usage helper methods.
#
# The result is one unified configuration file in data_management_module that the entire codebase can rely on,
# ensuring no duplication of config logic and preserving existing functionality.

import os
from configparser import ConfigParser
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataConfig:
    def __init__(self):
        self.config = ConfigParser()

        # Define base paths
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / 'data'
        self.log_dir = self.project_root / 'logs'

        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        # We will attempt to read a config file if it exists:
        config_file_path = self.project_root / 'config' / 'config.ini'
        if config_file_path.exists():
            self.config.read(config_file_path)
        else:
            print(f"Configuration file not found at {config_file_path}. Using environment variables and defaults.")

        # Step 1: define built-in defaults for the data management
        self._define_defaults()

        # Step 2: validate required fields from the original data config
        self._validate_config()

        # Step 3: incorporate the logic from the old trading_execution_engine config
        #         (Alpaca credentials, risk management, etc.)
        self._load_additional_alpaca_and_risk_settings()

    def _define_defaults(self):
        """
        Populate default settings for the 'DEFAULT' section 
        and the 'api' section if not already in the file/config.
        """
        # The default section
        if 'DEFAULT' not in self.config.sections():
            self.config['DEFAULT'] = {}

        default_dict = self.config['DEFAULT']
        default_dict.setdefault('database_path', str(self.data_dir / 'market_data.db'))
        default_dict.setdefault('tickers_file', str(self.data_dir / 'tickers.csv'))
        default_dict.setdefault('log_file', str(self.log_dir / 'data_manager.log'))
        default_dict.setdefault('historical_data_years', '5')
        default_dict.setdefault('data_frequency_minutes', '5')
        default_dict.setdefault('batch_size', '1000')
        default_dict.setdefault('zeromq_port', '5555')
        default_dict.setdefault('zeromq_topic', 'market_data')
        default_dict.setdefault('live_trading_mode', 'False')
        default_dict.setdefault('use_alpaca_store', 'False')
        default_dict.setdefault('live_trading_database_path', str(self.data_dir / 'live_trading_data.db'))

        # The 'api' section for data (if not present, create it)
        if 'api' not in self.config.sections():
            self.config.add_section('api')
        api_sec = self.config['api']
        api_sec.setdefault('base_url', 'https://data.alpaca.markets/v2')
        # Fill from env if present, otherwise fallback is empty string
        api_sec.setdefault('key_id', os.getenv('APCA_API_KEY_ID', ''))
        api_sec.setdefault('secret_key', os.getenv('APCA_API_SECRET_KEY', ''))
        api_sec.setdefault('rate_limit_retry_attempts', '3')
        api_sec.setdefault('rate_limit_retry_wait', '5')
        api_sec.setdefault('rate_limit_delay', '0.2')

        # The 'strategies' section (if missing)
        if 'strategies' not in self.config.sections():
            self.config.add_section('strategies')

    def _validate_config(self):
        """Validate critical configuration settings in the default section."""
        if not self.config['DEFAULT']['database_path']:
            raise ValueError("Database path missing from config")

    def _load_additional_alpaca_and_risk_settings(self):
        """
        Incorporate logic from the old trading_execution_engine config. 
        Reads environment variables or fallback config for:
            - Alpaca credentials
            - Risk management thresholds
            - Execution engine logging
        Then builds a final unified dictionary self.CONFIG that other modules can use.
        """

        # Create directories for logs/data if needed:
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)

        # If we find [alpaca] in the config file, we use those settings if env variables are not present
        config_file_fallback_base_url = self.config.get('alpaca', 'base_url', fallback='https://paper-api.alpaca.markets/v2') \
            if 'alpaca' in self.config.sections() else 'https://paper-api.alpaca.markets/v2'

        self.alpaca_base_url = os.getenv('APCA_API_BASE_URL', config_file_fallback_base_url)
        self.alpaca_key_id = os.getenv('APCA_API_KEY_ID',
                                       self.config.get('alpaca', 'key_id', fallback=None)
                                       if 'alpaca' in self.config.sections() else None)
        self.alpaca_secret_key = os.getenv('APCA_API_SECRET_KEY',
                                           self.config.get('alpaca', 'secret_key', fallback=None)
                                           if 'alpaca' in self.config.sections() else None)

        if not self.alpaca_key_id or not self.alpaca_secret_key:
            raise EnvironmentError("Alpaca API credentials not found. "
                                   "Please set environment variables or update the config file with [alpaca] key_id/secret_key.")

        # Risk management environment or config
        self.max_position_size_pct = float(
            os.getenv('MAX_POSITION_SIZE_PCT') or
            (self.config.get('risk', 'max_position_size_pct', fallback='0.1')
             if 'risk' in self.config.sections() else '0.1')
        )
        self.max_order_value = float(
            os.getenv('MAX_ORDER_VALUE') or
            (self.config.get('risk', 'max_order_value', fallback='50000.0')
             if 'risk' in self.config.sections() else '50000.0')
        )
        self.daily_loss_limit_pct = float(
            os.getenv('DAILY_LOSS_LIMIT_PCT') or
            (self.config.get('risk', 'daily_loss_limit_pct', fallback='0.02')
             if 'risk' in self.config.sections() else '0.02')
        )

        # Execution engine log file path
        # The old code used LOG_FILE = 'logs/execution_engine.log'
        # We'll unify it. If an environment var is set, use that; else fallback:
        self.execution_engine_log_file = os.getenv('EXECUTION_ENGINE_LOG_FILE',
                                                   str(Path('logs') / 'execution_engine.log'))

        # Build the final dictionary resembling the old CONFIG
        self.CONFIG = {
            'alpaca': {
                'base_url': self.alpaca_base_url,
                'key_id': self.alpaca_key_id,
                'secret_key': self.alpaca_secret_key
            },
            'logging': {
                'log_file': self.execution_engine_log_file
            },
            'database': {
                # from the old code: 'orders.db' for order manager
                'orders_db': os.path.join('data', 'orders.db')
            },
            'risk': {
                'max_position_size_pct': self.max_position_size_pct,
                'max_order_value': self.max_order_value,
                'daily_loss_limit_pct': self.daily_loss_limit_pct
            }
        }

    def get(self, section, key, fallback=None):
        """Get a configuration value from the underlying ConfigParser."""
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section, key):
        """Get an integer configuration value"""
        return self.config.getint(section, key)

    def get_float(self, section, key):
        """Get a float configuration value"""
        return self.config.getfloat(section, key)

    def sections(self):
        return self.config.sections()

    def items(self, section):
        return self.config.items(section)


# Instantiate a single global config instance
config = DataConfig()

# This dictionary is used by modules that previously imported from the second config file
# in the trading_execution_engine. We'll keep the name 'CONFIG' so references remain valid:
CONFIG = config.CONFIG


class UnifiedConfigLoader:
    """
    Loads global config, including both live and backtesting settings.
    Simplifies references so modules do not fetch environment variables directly.
    """

    @classmethod
    def get_backtest_setting(cls, key, default=None):
        """
        Example: Retrieve a backtest-related config from environment or default values.
        """
        if key == 'historical_data_years':
            # e.g. environment variable, or fallback
            return int(os.getenv('BACKTEST_DATA_YEARS', '5'))
        return default

    @classmethod
    def is_live_trading_mode(cls):
        """
        Already existing method to check if live trading mode is enabled.
        """
        val = os.getenv('LIVE_TRADING_MODE', 'False')
        return val.lower() in ['true', '1', 'yes']

    @classmethod
    def use_alpaca_store(cls):
        """
        If environment variable is set, override. Otherwise, fall back to 'use_alpaca_store'
        in the config's DEFAULT section.
        """
        env_val = os.getenv('USE_ALPACA_STORE', '')
        if env_val.lower() in ['true', '1', 'yes']:
            return True
        elif env_val.lower() in ['false', '0', 'no', '']:
            val = config.get('DEFAULT', 'use_alpaca_store', fallback='False').lower() == 'true'
            return val
        return False

    @classmethod
    def get_strategy_mode(cls, strategy_name):
        """
        Return 'live' or 'backtest' based on environment or config's 'strategies' section.
        If 'live_trading_mode' is not set or environment says no, default to 'backtest'.
        """
        if not cls.is_live_trading_mode():
            return 'backtest'
        mode = config.get('strategies', strategy_name, fallback='backtest').lower()
        if mode not in ['live', 'backtest']:
            mode = 'backtest'
        return mode

    @classmethod
    def set_strategy_mode(cls, strategy_name, new_mode):
        """
        Sets the strategy's mode in the config at runtime. E.g. 'live' or 'backtest'.
        """
        if new_mode not in ['live', 'backtest']:
            new_mode = 'backtest'
        config.config.set('strategies', strategy_name, new_mode)
        logger.info(f"set_strategy_mode: Strategy {strategy_name} mode set to {new_mode} in runtime config.")

    @classmethod
    def list_strategies(cls):
        """
        Lists known strategies from the config's 'strategies' section.
        """
        if 'strategies' in config.sections():
            return [item[0] for item in config.items('strategies')]
        return ['default_strategy']


# For easy import
__all__ = ['config', 'CONFIG', 'UnifiedConfigLoader']
