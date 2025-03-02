# File: components/backtesting_module/backtester.py
# Type: py

import backtrader as bt
import pandas as pd
import sqlite3
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from .config import BacktestConfig
from .exceptions import BacktestError, DataError
from .utils import validate_backtest_data
from components.backtesting_module.backtrader.benchmark_strategy import BenchmarkStrategy
from components.backtesting_module.backtrader.strategy_adapters import StrategyAdapter
from math import sqrt
import math
import matplotlib
matplotlib.use('Agg')  # Use Agg backend for environments without a display
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (12, 6)
plt.style.use('ggplot')  # a nice built-in style if you want a pretty look
from utils.find_project_root import find_project_root
import uuid
import io
import base64
from flask import current_app

# from components.data_management_module.config import UnifiedConfigLoader
# If suggestion #2 introduced a unified config approach for offline usage,
# we can keep a minimal import (only if we actually use it).
# Otherwise, remove it entirely.
# from components.data_management_module.config import config


logger = logging.getLogger(__name__)


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = find_project_root(current_dir, target_folder_name= 'ai_finance') # ai_smif_v3')# print(f"current_dir resolved to: {current_dir}")  
# print(f"project_root resolved to: {project_root}")  
logging.debug(f"Resolved project_root: {project_root}")


# Set logging level to DEBUG for detailed tracing
logging.basicConfig(
    filename='logs/backtesting.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)
logging.debug(f"Determined project_root as: {project_root}")


# Get path to Flask app root directory
app_root = current_app.root_path if current_app else os.path.join(os.path.dirname(__file__), '../ui_module/backend')

# Create plots directory in the app root
plots_dir = os.path.join(app_root, 'plots')
os.makedirs(plots_dir, exist_ok=True)


class AllInSizer(bt.Sizer):
    """
    A sizer that invests all available cash into the position on buy signals.
    """
    def _getsizing(self, comminfo, cash, data, isbuy):
        if isbuy:
            size = int(cash / data.close[0])
            return size if size > 0 else 0
        else:
            position = self.broker.getposition(data)
            return position.size

class PercentageInvestedObserver(bt.Observer):
    """
    Observer that prints the percentage of capital invested in the asset at each bar.
    """
    lines = ('percent_invested',)
    plotinfo = dict(plot=False)

    def next(self):
        value = self._owner.broker.getvalue()
        cash = self._owner.broker.getcash()
        invested_percent = (value - cash) / value * 100.0
        self.lines.percent_invested[0] = invested_percent
        current_date = self.datas[0].datetime.datetime(0)
        print(f"Date: {current_date}, Percent Invested: {invested_percent:.2f}%")


class Backtester:
    """
    Runs backtests using historical data and strategies from a local SQLite database.
    This backtester does NOT reference or check 'live trading' mode at all.
    """

    def __init__(self, strategy_name, strategy_params, ticker, start_date=None, end_date=None, db_path=os.path.join(project_root, 'data', 'market_data.db'), percent_invest=100,
                 stop_loss=0.0, take_profit=0.0):
        self.logger = logging.getLogger('Backtester')
        # self.historical_years = UnifiedConfigLoader.get_backtest_setting('historical_data_years', default=5)
        # self.logger.info(f"Using historical_data_years from UnifiedConfigLoader = {self.historical_years}")
        self.strategy_name = strategy_name
        self.strategy_params = strategy_params
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.results = None
        self.final_value = None
        self.db_path = db_path
        self.percent_invest = percent_invest
        self.stop_loss = stop_loss
        self.take_profit = take_profit

        self._set_default_dates_if_needed()
        self.plot_filename = None  # if we generate a plot, store the path here

        
        # Example usage: unify or override the date range using config
        # This is optional, but here is an illustration:
        # years = UnifiedConfigLoader.get_backtest_setting('historical_data_years', default=5)
        # self.logger.info(f"Using historical_data_years from UnifiedConfigLoader = {years}.")

        # Potentially we can override start_date if needed
        # (not necessarily recommended, but here's how you'd do it)
        # if not self.start_date:
        #     self.start_date = datetime.now() - timedelta(days=365 * years)

    def _set_default_dates_if_needed(self):
        self.logger.debug("Setting default dates if needed")
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT MIN(timestamp) as min_ts, MAX(timestamp) as max_ts
            FROM historical_data
            WHERE ticker_symbol = ?
        """
        row = conn.execute(query, (self.ticker,)).fetchone()
        conn.close()

        if not row or row[0] is None or row[1] is None:
            raise DataError(f"No data found for ticker {self.ticker} in the database.")

        min_ts, max_ts = row
        min_ts = pd.to_datetime(min_ts)
        max_ts = pd.to_datetime(max_ts)

        if self.start_date is None:
            self.start_date = min_ts
        if self.end_date is None:
            self.end_date = max_ts

        self.logger.info(f"Date range set to {self.start_date} - {self.end_date} for {self.ticker}")

    def load_data(self):
        logging.info(f"Loading data for {self.ticker} from {self.start_date} to {self.end_date}")

        start_str = self.start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_str = self.end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE ticker_symbol = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql(query, conn, params=(self.ticker, start_str, end_str))
        conn.close()

        if df.empty:
            raise DataError(f"No data found for {self.ticker} between {self.start_date} and {self.end_date}")

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        self.data = df
        logging.info(f"Data loaded: {len(self.data)} rows.")
        print("Data Loaded:")
        print("First Rows:\n", self.data.head())
        print("Last Rows:\n", self.data.tail())
        print(f"Date Range for the test: {self.start_date} to {self.end_date}")
        print(f"Total bars: {len(self.data)}")

    def run_backtest(self):
        try:
            # Must set Agg backend before importing pyplot
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            logger.info(
            f"Running backtest for {self.ticker} from {self.start_date} to {self.end_date}, "
            f"strategy={self.strategy_name}"
            )
            
            self.logger.debug("Starting run_backtest method...")
            self.load_data()
            logging.debug("Data loaded successfully. Validating data...")
            validate_backtest_data(self.data)
            logging.debug("Data validation passed. Setting up cerebro...")

            cerebro = bt.Cerebro()

            data_feed = bt.feeds.PandasData(
                dataname=self.data,
                timeframe=bt.TimeFrame.Minutes,
                compression=5
            )
            cerebro.adddata(data_feed)

            strategy_class = StrategyAdapter.get_strategy(self.strategy_name)
            
            # Make a copy of strategy_params to avoid modifying the original
            strategy_params_copy = self.strategy_params.copy()
            
            # Remove parameters that the strategy doesn't accept
            if 'start_date' in strategy_params_copy:
                strategy_params_copy.pop('start_date')
            if 'end_date' in strategy_params_copy:
                strategy_params_copy.pop('end_date')
            if 'timeframe' in strategy_params_copy:
                strategy_params_copy.pop('timeframe')
            
            # Add the strategy with the filtered parameters
            cerebro.addstrategy(strategy_class, **strategy_params_copy)

            cerebro.addsizer(bt.sizers.PercentSizer, percents=self.percent_invest)
            cerebro.broker.setcash(100000.0)
            cerebro.broker.setcommission(commission=0.0)
            cerebro.broker.set_slippage_perc(0.0)

            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
            cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')

            logging.debug("Running cerebro...")
            results = cerebro.run()
            self.final_value = cerebro.broker.getvalue()
            logging.debug(f"Cerebro run completed. Final portfolio value: {self.final_value}")

            # Extract analyzer results
            logging.debug("Extracting analyzer results...")
            analyzer = results[0].analyzers
            returns_analysis = analyzer.returns.get_analysis()
            sharpe_analysis = analyzer.sharpe.get_analysis()
            drawdown_analysis = analyzer.drawdown.get_analysis()
            trade_analysis = analyzer.trades.get_analysis()
            annual_return_analysis = analyzer.annualreturn.get_analysis()
            time_return_analysis = analyzer.timereturn.get_analysis()
            sqn_analysis = analyzer.sqn.get_analysis()

            total_return = returns_analysis['rtot']
            total_pct_change = total_return * 100.0
            initial_cash = 100000.0
            total_pl = self.final_value - initial_cash

            days = (self.end_date - self.start_date).days
            years = days / 365.0
            if years > 0:
                cagr = (self.final_value / initial_cash) ** (1 / years) - 1
            else:
                cagr = None

            daily_rets = pd.Series(time_return_analysis)
            daily_rets.index = pd.to_datetime(daily_rets.index)
            std_dev = daily_rets.std()
            annual_vol = std_dev * math.sqrt(252)

            negative_returns = daily_rets[daily_rets < 0]
            if len(negative_returns) > 0:
                downside_dev = negative_returns.std()
                sortino_ratio = (daily_rets.mean() * 252) / (downside_dev * math.sqrt(252))
            else:
                sortino_ratio = None
            total_trades = trade_analysis.total.total if 'total' in trade_analysis and 'total' in trade_analysis.total else 0
            won_trades = trade_analysis.won.total if 'won' in trade_analysis and 'total' in trade_analysis.won else 0
            win_rate = (won_trades / total_trades * 100.0) if total_trades > 0 else None

            benchmark_ticker = BacktestConfig.BENCHMARK_TICKER
            benchmark_metrics = self.run_benchmark(benchmark_ticker)
            benchmark_return = benchmark_metrics['Total Return']

            alpha = (total_return - benchmark_return) * 100.0

            benchmark_daily = self.get_benchmark_daily_returns(benchmark_ticker)
            combined = pd.concat([daily_rets, benchmark_daily], axis=1).dropna()
            combined.columns = ['strategy', 'benchmark']
            excess_return = combined['strategy'] - combined['benchmark']
            if excess_return.std() != 0:
                information_ratio = (
                    (excess_return.mean() * math.sqrt(252))
                    / (excess_return.std() * math.sqrt(252))
                )
            else:
                information_ratio = None

            sharpe_ratio = sharpe_analysis.get('sharperatio', None)
            max_drawdown = drawdown_analysis['max']['drawdown']

            logging.debug("Saving results to DB...")
            self.save_results_to_db(
                strategy_name=self.strategy_name,
                strategy_params=self.strategy_params,
                ticker=self.ticker,
                start_date=self.start_date,
                end_date=self.end_date,
                final_value=self.final_value,
                total_pl=total_pl,
                total_pct_change=total_pct_change,
                cagr=cagr,
                total_return=total_return,
                std_dev=std_dev,
                annual_vol=annual_vol,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                alpha=alpha,
                num_trades=total_trades,
                information_ratio=information_ratio
            )
            logging.debug("Results saved to DB successfully.")

            # Create directory for plots if it doesn't exist
            static_dir = os.path.join('components', 'ui_module', 'backend', 'static', 'plots')
            os.makedirs(static_dir, exist_ok=True)
            
            # Generate unique filename
            plot_filename = f"backtest_{self.ticker}_{uuid.uuid4().hex[:8]}.png"
            plot_path = os.path.join(static_dir, plot_filename)
            
            # Save figure to file and close it
            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Plot the data using simple matplotlib commands
            # This example just plots close prices - adjust based on your data structure
            if results and len(results) > 0:
                strategy = results[0]
                dates = [bt.num2date(x) for x in strategy.data.datetime.get(size=len(strategy.data))]
                closes = strategy.data.close.get(size=len(strategy.data))
                ax.plot(dates, closes, label='Close')
                ax.set_title(f'Backtest for {self.ticker} using {self.strategy_name}')
                ax.set_xlabel('Date')
                ax.set_ylabel('Price')
                ax.legend()
            
            fig.savefig(plot_path)
            plt.close(fig)
            
            # Debug logs
            print(f"Plot saved to: {plot_path}")
            print(f"File exists: {os.path.exists(plot_path)}")
            
            # Return the URL matching the Flask route
            plot_url = f"http://localhost:5001/plots/{plot_filename}"
            
            # Return with proper URL
            return {
                'success': True,
                'plot_url': plot_url,
                'metrics': {
                    'total_pl': total_pl,
                    'total_pct_change': total_pct_change,
                    'cagr': cagr,
                    'total_return': total_return,
                    'sharpe_ratio': sharpe_ratio,
                    'sortino_ratio': sortino_ratio,
                    'max_drawdown': max_drawdown,
                    'win_rate': win_rate,
                    'num_trades': total_trades,
                    'information_ratio': information_ratio
                } if results and len(results) > 0 else {}
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    def save_results_to_db(self, strategy_name, strategy_params, ticker, start_date, end_date,
                           final_value, total_pl, total_pct_change, cagr, total_return,
                           std_dev, annual_vol, sharpe_ratio, sortino_ratio, max_drawdown,
                           win_rate, alpha, num_trades, information_ratio):
        logging.debug("Entering save_results_to_db...")
        conn = sqlite3.connect(os.path.join(project_root, 'data', 'backtesting_results.db'))
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT,
                strategy_params TEXT,
                ticker TEXT,
                start_date TEXT,
                end_date TEXT,
                final_value REAL,
                total_pl REAL,
                total_pct_change REAL,
                cagr REAL,
                total_return REAL,
                std_dev REAL,
                annual_vol REAL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                alpha REAL,
                num_trades INTEGER,
                information_ratio REAL,
                strategy_unique_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        param_str = "_".join([f"{k}{v}" for k, v in sorted(strategy_params.items())])
        run_timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = f"{strategy_name}_{ticker}_{param_str}_{run_timestamp}"

        cursor.execute('''
            INSERT INTO backtest_summary (
                strategy_name, strategy_params, ticker, start_date, end_date,
                final_value, total_pl, total_pct_change, cagr, total_return,
                std_dev, annual_vol, sharpe_ratio, sortino_ratio, max_drawdown,
                win_rate, alpha, num_trades, information_ratio, strategy_unique_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            strategy_name,
            json.dumps(strategy_params),
            ticker,
            start_date.strftime('%Y-%m-%d %H:%M:%S'),
            end_date.strftime('%Y-%m-%d %H:%M:%S'),
            final_value,
            total_pl,
            total_pct_change,
            cagr if cagr is not None else None,
            total_return,
            std_dev if not pd.isna(std_dev) else None,
            annual_vol if not pd.isna(annual_vol) else None,
            sharpe_ratio,
            sortino_ratio if sortino_ratio is not None else None,
            max_drawdown,
            win_rate,
            alpha,
            num_trades,
            information_ratio,
            unique_id
        ))
        conn.commit()
        conn.close()
        logging.debug("Backtest summary saved to DB.")

    def get_benchmark_daily_returns(self, benchmark_ticker):
        if hasattr(self, 'benchmark_daily_returns'):
            ser = pd.Series(self.benchmark_daily_returns)
            ser.index = pd.to_datetime(ser.index)
            return ser
        else:
            self.run_benchmark(benchmark_ticker)
            ser = pd.Series(self.benchmark_daily_returns)
            ser.index = pd.to_datetime(ser.index)
            return ser

    def save_results(self, plot_filename=None):
        if not os.path.exists('data/results'):
            os.makedirs('data/results')
        conn = sqlite3.connect('data/results/backtest_results.db')
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
        returns_analysis = analyzer.returns.get_analysis()
        sharpe_analysis = analyzer.sharpe.get_analysis()
        drawdown_analysis = analyzer.drawdown.get_analysis()

        total_return = returns_analysis['rtot']
        sharpe_ratio = sharpe_analysis.get('sharperatio', None)
        max_drawdown = drawdown_analysis['max']['drawdown']

        cursor.execute('''
            INSERT INTO backtest_results (
                strategy_name, strategy_params, ticker, start_date, end_date,
                final_value, total_return, sharpe_ratio, max_drawdown
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.strategy_name,
            json.dumps(self.strategy_params),
            self.ticker,
            self.start_date.strftime('%Y-%m-%d %H:%M:%S'),
            self.end_date.strftime('%Y-%m-%d %H:%M:%S'),
            self.final_value,
            total_return,
            sharpe_ratio,
            max_drawdown
        ))
        conn.commit()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_plots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id INTEGER,
                plot_file TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(backtest_id) REFERENCES backtest_results(id)
            )
        ''')

        backtest_id = cursor.lastrowid

        if plot_filename is not None:
            cursor.execute('''
                INSERT INTO backtest_plots (backtest_id, plot_file)
                VALUES (?, ?)
            ''', (backtest_id, plot_filename))
            conn.commit()

        conn.close()

    def get_performance_metrics(self):
        analyzer = self.results[0].analyzers

        final_value = self.final_value
        returns_analysis = analyzer.returns.get_analysis()
        sharpe_analysis = analyzer.sharpe.get_analysis()
        drawdown_analysis = analyzer.drawdown.get_analysis()
        annual_return_analysis = analyzer.annualreturn.get_analysis()
        time_return_analysis = analyzer.timereturn.get_analysis()
        sqn_analysis = analyzer.sqn.get_analysis()
        trade_analysis = analyzer.trades.get_analysis()
        total_trades = trade_analysis.total.total if 'total' in trade_analysis and 'total' in trade_analysis.total else None
        won_trades = trade_analysis.won.total if 'won' in trade_analysis and 'total' in trade_analysis.won else None
        win_rate = None
        if won_trades is not None and total_trades is not None and total_trades > 0:
            win_rate = (won_trades / total_trades) * 100.0

        metrics = {
            'Final Portfolio Value': final_value,
            'Total Return': returns_analysis['rtot'],
            'Total % Return': returns_analysis['rtot'] * 100,
            'Sharpe Ratio': sharpe_analysis.get('sharperatio', None),
            'Max Drawdown': drawdown_analysis['max']['drawdown'],
            'Annual Returns': annual_return_analysis,
            'Daily Returns': time_return_analysis,
            'SQN': sqn_analysis['sqn'] if 'sqn' in sqn_analysis else None,
            'Number of Trades': total_trades,
            'Win Rate (%)': win_rate
        }

        return metrics

    def save_plot_filename(self, plot_filename):
        with sqlite3.connect(os.path.join(project_root, 'data', 'backtesting_results.db')) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_plots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backtest_id INTEGER,
                    plot_file TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(backtest_id) REFERENCES backtest_summary(id)
                )
            ''')

            cursor.execute("SELECT MAX(id) FROM backtest_summary")
            result = cursor.fetchone()
            backtest_id = result[0] if result else None

            if backtest_id is not None:
                cursor.execute('''
                    INSERT INTO backtest_plots (backtest_id, plot_file)
                    VALUES (?, ?)
                ''', (backtest_id, plot_filename))
                conn.commit()
            else:
                logging.warning("No backtest record found to associate the plot with.")


    def run_benchmark(self, benchmark_ticker, cash=100000.0, commission=0.0):
        conn = sqlite3.connect(self.db_path)
        start_str = self.start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_str = self.end_date.strftime('%Y-%m-%d %H:%M:%S')
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE ticker_symbol = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp ASC
        """
        benchmark_data = pd.read_sql(query, conn, params=(benchmark_ticker, start_str, end_str))
        conn.close()

        if benchmark_data.empty:
            raise DataError(f"No benchmark data found for {benchmark_ticker} between {self.start_date} and {self.end_date}")

        benchmark_data['timestamp'] = pd.to_datetime(benchmark_data['timestamp'])
        benchmark_data.set_index('timestamp', inplace=True)

        cerebro = bt.Cerebro()
        data_feed = bt.feeds.PandasData(
            dataname=benchmark_data,
            timeframe=bt.TimeFrame.Minutes,
            compression=5
        )
        cerebro.adddata(data_feed)
        cerebro.addstrategy(BenchmarkStrategy)
        cerebro.addsizer(bt.sizers.PercentSizer, percents=100)

        cerebro.broker.setcash(cash)
        cerebro.broker.setcommission(commission=commission)
        cerebro.broker.set_slippage_perc(0.0)

        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')

        benchmark_results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        analyzer = benchmark_results[0].analyzers

        returns_analysis = analyzer.returns.get_analysis()
        sharpe_analysis = analyzer.sharpe.get_analysis()
        drawdown_analysis = analyzer.drawdown.get_analysis()

        self.benchmark_daily_returns = analyzer.timereturn.get_analysis()

        metrics = {
            'Final Portfolio Value': final_value,
            'Total Return': returns_analysis['rtot'],
            'Sharpe Ratio': sharpe_analysis.get('sharperatio', None),
            'Max Drawdown': drawdown_analysis['max']['drawdown']
        }
        return metrics

    def compare_with_benchmark(self, benchmark_ticker='SPY'):
        strategy_metrics = self.get_performance_metrics()
        benchmark_metrics = self.run_benchmark(benchmark_ticker)

        print("=== Comparison ===")
        print("Strategy:", strategy_metrics)
        print("Benchmark:", benchmark_metrics)

        return {
            'Strategy': strategy_metrics,
            'Benchmark': benchmark_metrics
        }
