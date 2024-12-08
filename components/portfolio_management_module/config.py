# components/portfolio_management_module/config.py

import configparser
import os

config = configparser.ConfigParser()

# Load the configuration file or create defaults
config_file_path = os.path.join(os.path.dirname(__file__), 'portfolio_config.ini')
if os.path.exists(config_file_path):
    config.read(config_file_path)
else:
    config['PORTFOLIO'] = {
        'DEFAULT_ALLOCATION_PER_STRATEGY': '5000'
    }
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

DEFAULT_ALLOCATION_PER_STRATEGY = float(config['PORTFOLIO'].get('DEFAULT_ALLOCATION_PER_STRATEGY', '5000'))
