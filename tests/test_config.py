# tests/test_config.py

TEST_CONFIG = {
    'alpaca': {
        'base_url': 'https://paper-api.alpaca.markets',
        'key_id': 'test_key',
        'secret_key': 'test_secret'
    },
    'risk': {
        'max_position_size_pct': 0.1,
        'max_order_value': 50000,
        'daily_loss_limit_pct': 0.02
    },
    'logging': {
        'log_file': 'tests/test_execution_engine.log'
    },
    'database': {
        'orders_db': ':memory:'  # Use in-memory database for tests
    }
}