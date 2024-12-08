# components/reporting_analytics_module/config.py

import configparser
import os

config = configparser.ConfigParser()

config_file_path = os.path.join(os.path.dirname(__file__), 'reporting_analytics_config.ini')
if os.path.exists(config_file_path):
    config.read(config_file_path)
else:
    config['REPORTING'] = {
        'REPORT_DIRECTORY': 'reports',
        'DEFAULT_REPORT_FORMAT': 'html'
    }
    with open(config_file_path, 'w') as configfile:
        config.write(configfile)

REPORT_DIRECTORY = config['REPORTING'].get('REPORT_DIRECTORY', 'reports')
DEFAULT_REPORT_FORMAT = config['REPORTING'].get('DEFAULT_REPORT_FORMAT', 'html')
