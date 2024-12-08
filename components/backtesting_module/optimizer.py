# components/backtesting_module/optimizer.py

import backtrader as bt
from components.backtesting_module.strategy_adapters import StrategyAdapter
from components.data_management_module.alpaca_api import AlpacaAPIClient
from datetime import datetime
import pandas as pd
import logging
from itertools import product

logging.basicConfig(
    filename='logs/optimizer.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

class Optimizer:
    """
    Performs parameter optimization (grid search).
    """

    def __init__(self, strategy_name, ticker, start_date, end_date):
        self.strategy_name = strategy_name
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
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
                timeframe='1Day'
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

    def run_optimization(self, param_ranges, cash=100000.0, commission=0.001, max_combinations=100):
        self.load_data()
        cerebro = bt.Cerebro(optreturn=False)
        data_feed = bt.feeds.PandasData(dataname=self.data)
        cerebro.adddata(data_feed)

        # Generate parameter combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = list(product(*param_values))

        # Limit combinations to prevent overload
        if len(combinations) > max_combinations:
            logging.warning(f"Limiting combinations to first {max_combinations} due to resource constraints.")
            combinations = combinations[:max_combinations]

        cerebro.optstrategy(
            StrategyAdapter,
            strategy_name=self.strategy_name,
            strategy_params=[
                dict(zip(param_names, combination)) for combination in combinations
            ]
        )
        cerebro.broker.setcash(cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        logging.info(f"Starting optimization for {self.strategy_name} on {self.ticker}")
        optimized_runs = cerebro.run(maxcpus=1)
        logging.info("Optimization completed.")
        return self.collect_results(optimized_runs)

    def collect_results(self, optimized_runs):
        optimization_results = []
        for run in optimized_runs:
            for strategy in run:
                params = strategy.params.strategy_params
                sharpe = strategy.analyzers.sharpe.get_analysis().get('sharperatio', None)
                drawdown = strategy.analyzers.drawdown.get_analysis()['max']['drawdown']
                total_return = strategy.analyzers.returns.get_analysis()['rtot']
                optimization_results.append({
                    'params': params,
                    'sharpe_ratio': sharpe,
                    'max_drawdown': drawdown,
                    'total_return': total_return
                })
        return optimization_results

    def get_best_params(self, optimization_results, metric='sharpe_ratio'):
        df = pd.DataFrame(optimization_results)
        df = df.dropna(subset=[metric])
        if df.empty:
            raise ValueError("No valid optimization results to select best parameters.")
        best_row = df.loc[df[metric].idxmax()]
        return best_row['params']
