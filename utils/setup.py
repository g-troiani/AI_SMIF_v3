# setup.py

from setuptools import setup, find_packages

setup(
    name="ai-smif-v2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'alpaca-trade-api>=2.5.0',
        'backtrader>=1.9.78',
        'pandas>=1.5.3',
        'numpy>=1.24.3',
        'pytest>=7.4.0',
        'yfinance>=0.2.28',
        'python-dotenv>=1.0.0',
        'SQLAlchemy>=2.0.0',
        'requests>=2.31.0',
        'aiohttp>=3.9.1',
        'pyzmq>=25.1.1',
        'Flask>=2.3.3',
        'Flask-SocketIO>=5.3.6',
        'Flask-Bootstrap>=3.3.7',
        'Jinja2>=3.1.2',
        'pytest-asyncio>=0.21.1'
    ],
    python_requires='>=3.8',
)