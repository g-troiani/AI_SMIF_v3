# components/backtesting_module/backtester.py

import backtrader as bt
from components.backtesting_module.strategy_adapters import StrategyAdapter
from components.data_management_module.alpaca_api import AlpacaAPIClient
from datetime import datetime
import os
import sqlite3
import json
import logging
from .config import BacktestConfig
from .exceptions import BacktestError, DataError
from .utils import validate_backtest_data, calculate_statistics

logging.basicConfig(
    filename='logs/backtesting.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

class Backtester:
    """
    Runs backtests using historical data and strategies.
    """

    def __init__(self, strategy_name, strategy_params, ticker, start_date, end_date):
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = None
        self.final_value = None
        self.alpaca_client = AlpacaAPIClient()

    def load_data(self):
        """
        Fetches historical data from the Alpaca API.
        """
        logging.info(f"Fetching data for {self.ticker} from {self.start_date} to {self.end_date}")
        try:
            self.data = self.alpaca_client.fetch_historical_data(
                self.ticker,
                self.start_date,
                self.end_date,
                timeframe='1Day'  # Adjust timeframe as needed
            )
            if self.data.empty:
                raise ValueError(f"No data found for ticker {self.ticker} between {self.start_date} and {self.end_date}")
            self.data.rename(columns={
                't': 'datetime',
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            }, inplace=True)
            self.data.set_index('datetime', inplace=True)
            self.data.index = pd.to_datetime(self.data.index)
        except Exception as e:
            logging.error(f"Error fetching data: {e}")
            raise

    # In components/backtesting_module/backtester.py
    # Update the run_backtest method:

    def run_backtest(self, cash=100000.0, commission=0.001):
        try:
            self.load_data()
            cerebro = bt.Cerebro()
            data_feed = bt.feeds.PandasData(dataname=self.data)
            cerebro.adddata(data_feed)
            
            # Get strategy class from adapter
            strategy_class = StrategyAdapter.get_strategy(self.strategy_name)
            cerebro.addstrategy(strategy_class, **self.strategy_params)
            
            cerebro.broker.setcash(cash)
            cerebro.broker.setcommission(commission=commission)
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            
            logging.info(f"Starting backtest for {self.strategy_name} on {self.ticker}")
            self.results = cerebro.run()
            self.final_value = cerebro.broker.getvalue()
            logging.info(f"Backtest completed. Final portfolio value: {self.final_value}")
        except Exception as e:
            logging.error(f"Error during backtest: {e}")
            raise

    def save_results(self):
        if not os.path.exists('components/backtesting_module/results'):
            os.makedirs('components/backtesting_module/results')
        conn = sqlite3.connect('components/backtesting_module/results/backtest_results.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                strategy_params TEXT,
                ticker TEXT,
                start_date TEXT,
                end_date TEXT,
                final_value REAL,
                total_return REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        analyzer = self.results[0].analyzers
        total_return = analyzer.returns.get_analysis()['rtot']
        sharpe_ratio = analyzer.sharpe.get_analysis().get('sharperatio', None)
        max_drawdown = analyzer.drawdown.get_analysis()['max']['drawdown']

        cursor.execute('''
            INSERT INTO backtest_results (
                strategy_name, strategy_params, ticker, start_date, end_date,
                final_value, total_return, sharpe_ratio, max_drawdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.strategy_name,
            json.dumps(self.strategy_params),
            self.ticker,
            self.start_date.strftime('%Y-%m-%d'),
            self.end_date.strftime('%Y-%m-%d'),
            self.final_value,
            total_return,
            sharpe_ratio,
            max_drawdown
        ))
        conn.commit()
        conn.close()

    def get_performance_metrics(self):
        analyzer = self.results[0].analyzers
        metrics = {
            'Final Portfolio Value': self.final_value,
            'Total Return': analyzer.returns.get_analysis()['rtot'],
            'Sharpe Ratio': analyzer.sharpe.get_analysis().get('sharperatio', None),
            'Max Drawdown': analyzer.drawdown.get_analysis()['max']['drawdown']
        }
        return metrics

    def run_benchmark(self, benchmark_ticker, cash=100000.0, commission=0.001):
        try:
            logging.info(f"Fetching benchmark data for {benchmark_ticker}")
            benchmark_data = self.alpaca_client.fetch_historical_data(
                benchmark_ticker,
                self.start_date,
                self.end_date,
                timeframe='1Day'
            )
            if benchmark_data.empty:
                raise ValueError(f"No data found for benchmark ticker {benchmark_ticker} between {self.start_date} and {self.end_date}")
            benchmark_data.rename(columns={
                't': 'datetime',
                'o': 'open',
                'h': 'high',
                'l': 'low',
                'c': 'close',
                'v': 'volume'
            }, inplace=True)
            benchmark_data.set_index('datetime', inplace=True)
            benchmark_data.index = pd.to_datetime(benchmark_data.index)

            cerebro = bt.Cerebro()
            data_feed = bt.feeds.PandasData(dataname=benchmark_data)
            cerebro.adddata(data_feed)
            cerebro.addstrategy(BenchmarkStrategy)
            cerebro.broker.setcash(cash)
            cerebro.broker.setcommission(commission=commission)
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            benchmark_results = cerebro.run()
            final_value = cerebro.broker.getvalue()
            analyzer = benchmark_results[0].analyzers
            metrics = {
                'Final Portfolio Value': final_value,
                'Total Return': analyzer.returns.get_analysis()['rtot'],
                'Sharpe Ratio': analyzer.sharpe.get_analysis().get('sharperatio', None),
                'Max Drawdown': analyzer.drawdown.get_analysis()['max']['drawdown']
            }
            return metrics
        except Exception as e:
            logging.error(f"Error during benchmark backtest: {e}")
            raise

    def compare_with_benchmark(self, benchmark_ticker='SPY'):
        strategy_metrics = self.get_performance_metrics()
        benchmark_metrics = self.run_benchmark(benchmark_ticker)

        comparison = {
            'Strategy': strategy_metrics,
            'Benchmark': benchmark_metrics
        }
        return comparison
