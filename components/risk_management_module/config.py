# components/risk_management_module/config.py

import configparser
import os

config = configparser.ConfigParser()

# Load or create a configuration file
config_file_path = os.path.join(os.path.dirname(__file__), 'risk_management_config.ini')
if os.path.exists(config_file_path):
    config.read(config_file_path)
else:
    config['RISK'] = {
        'DEFAULT_STOP_LOSS_PERCENT': '10',
        'DEFAULT_TAKE_PROFIT_PERCENT': '20',
        'MAX_DRAW_DOWN_PERCENT': '20'
    }
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

DEFAULT_STOP_LOSS_PERCENT = float(config['RISK'].get('DEFAULT_STOP_LOSS_PERCENT', '10'))
DEFAULT_TAKE_PROFIT_PERCENT = float(config['RISK'].get('DEFAULT_TAKE_PROFIT_PERCENT', '20'))
MAX_DRAW_DOWN_PERCENT = float(config['RISK'].get('MAX_DRAW_DOWN_PERCENT', '20'))
