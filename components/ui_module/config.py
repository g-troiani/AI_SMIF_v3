# components/ui_module/config.py
import os
from secrets import token_hex

SECRET_KEY = os.environ.get('SECRET_KEY') or token_hex(16)
DEBUG = True  # For development only