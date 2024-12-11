import backtrader as bt
import pandas as pd
import sqlite3
import json
import logging
import os
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

logging.basicConfig(
    filename='logs/backtesting.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

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
    """

    def __init__(self, strategy_name, strategy_params, ticker, start_date=None, end_date=None, db_path='data/market_data.db', percent_invest=100,
                 stop_loss=0.0, take_profit=0.0):
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


    def _set_default_dates_if_needed(self):
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

        logging.info(f"Date range set to {self.start_date} - {self.end_date} for {self.ticker}")

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

    def run_backtest(self, cash=100000.0, commission=0.0):
        try:
            self.load_data()
            validate_backtest_data(self.data)
            cerebro = bt.Cerebro()

            data_feed = bt.feeds.PandasData(
                dataname=self.data,
                timeframe=bt.TimeFrame.Minutes,
                compression=5
            )
            cerebro.adddata(data_feed)

            # Add strategy with stop_loss and take_profit as params
            strategy_class = StrategyAdapter.get_strategy(self.strategy_name)
            cerebro.addstrategy(strategy_class, 
                                stop_loss=self.stop_loss, 
                                take_profit=self.take_profit, 
                                **self.strategy_params
                                )

            cerebro.addsizer(bt.sizers.PercentSizer, percents=self.percent_invest)
            cerebro.broker.setcash(cash)
            cerebro.broker.setcommission(commission=commission)
            cerebro.broker.set_slippage_perc(0.0)

            # Add analyzers
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn')
            cerebro.addanalyzer(bt.analyzers.SQN, _name='sqn')

            # Run backtest
            self.results = cerebro.run()
            self.final_value = cerebro.broker.getvalue()

            # Extract analyzer results
            analyzer = self.results[0].analyzers
            returns_analysis = analyzer.returns.get_analysis()
            sharpe_analysis = analyzer.sharpe.get_analysis()
            drawdown_analysis = analyzer.drawdown.get_analysis()
            trade_analysis = analyzer.trades.get_analysis()
            annual_return_analysis = analyzer.annualreturn.get_analysis()
            time_return_analysis = analyzer.timereturn.get_analysis()
            sqn_analysis = analyzer.sqn.get_analysis()

            # Compute additional metrics
            total_return = returns_analysis['rtot']          # cumulative return (decimal)
            total_pct_change = total_return * 100.0
            initial_cash = cash
            total_pl = self.final_value - initial_cash

            days = (self.end_date - self.start_date).days
            years = days / 365.0
            cagr = ((self.final_value / initial_cash) ** (1 / years) - 1) if years > 0 else None

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
            benchmark_metrics = self.run_benchmark(benchmark_ticker, cash=cash, commission=commission)
            benchmark_return = benchmark_metrics['Total Return'] # decimal form

            alpha = (total_return - benchmark_return) * 100.0

            benchmark_daily = self.get_benchmark_daily_returns(benchmark_ticker)
            combined = pd.concat([daily_rets, benchmark_daily], axis=1).dropna()
            combined.columns = ['strategy', 'benchmark']
            excess_return = combined['strategy'] - combined['benchmark']
            information_ratio = ((excess_return.mean() * math.sqrt(252)) / (excess_return.std() * math.sqrt(252))) if excess_return.std() != 0 else None

            sharpe_ratio = sharpe_analysis.get('sharperatio', None)
            max_drawdown = drawdown_analysis['max']['drawdown']

            # Save results to new database
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

            # Ensure plots directory exists
            if not os.path.exists('plots'):
                os.makedirs('plots')
            plot_filename = f"plots/backtest_plot_{self.strategy_name}_{self.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            # Make the plot prettier
            # Set a nicer style
            figs = cerebro.plot(style='candle', barup='green', bardown='red', volume=False)
            fig = figs[0][0]

            # Customize figure
            fig.suptitle(f"Backtest Result - {self.strategy_name} on {self.ticker}", fontsize=16, fontweight='bold')
            fig.savefig(plot_filename, dpi=300, bbox_inches='tight')
            plt.close(fig)

            self.save_plot_filename(plot_filename)

        except Exception as e:
            logging.error(f"Error during backtest: {e}")
            raise


            # Save results to new database
    def save_results_to_db(self, strategy_name, strategy_params, ticker, start_date, end_date,
                           final_value, total_pl, total_pct_change, cagr, total_return,
                           std_dev, annual_vol, sharpe_ratio, sortino_ratio, max_drawdown,
                           win_rate, alpha, num_trades, information_ratio):
        
        # Use data/backtesting_results.db for the main summary database
        conn = sqlite3.connect('data/backtesting_results.db')
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

        # Generate a unique identifier by combining strategy_name, ticker, params, and timestamp
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


    def get_benchmark_daily_returns(self, benchmark_ticker):
        if hasattr(self, 'benchmark_daily_returns'):
            ser = pd.Series(self.benchmark_daily_returns)
            ser.index = pd.to_datetime(ser.index)
            return ser
        else:
            # If not run yet, run benchmark now
            self.run_benchmark(benchmark_ticker)
            ser = pd.Series(self.benchmark_daily_returns)
            ser.index = pd.to_datetime(ser.index)
            return ser

    def get_benchmark_daily_returns(self, benchmark_ticker):
        if hasattr(self, 'benchmark_daily_returns'):
            ser = pd.Series(self.benchmark_daily_returns)
            ser.index = pd.to_datetime(ser.index)
            return ser
        else:
            # If not run yet, run benchmark now
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

        # New table for saving plot results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_plots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id INTEGER,
                plot_file TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(backtest_id) REFERENCES backtest_results(id)
            )
        ''')

        # Get the last inserted backtest_id
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

        # Extract existing metrics
        final_value = self.final_value
        returns_analysis = analyzer.returns.get_analysis()
        sharpe_analysis = analyzer.sharpe.get_analysis()
        drawdown_analysis = analyzer.drawdown.get_analysis()

        # Extract additional metrics from newly added analyzers
        # annualreturn: a dict of year: return
        annual_return_analysis = analyzer.annualreturn.get_analysis()
        # timereturn: daily returns as a dict {datetime: return}
        time_return_analysis = analyzer.timereturn.get_analysis()
        # sqn: SQN value
        sqn_analysis = analyzer.sqn.get_analysis()

        # Note: The user requested many metrics. Some are not directly available out-of-the-box.
        # Below we report what we can from the analyzers we've added:
        # - Final Portfolio Value: final_value
        # - Total Return: returns_analysis['rtot']
        # - Sharpe Ratio: sharpe_analysis.get('sharperatio', None)
        # - Max Drawdown: drawdown_analysis['max']['drawdown']
        # - Annual Returns (from AnnualReturn): annual_return_analysis
        # - Daily Returns (from TimeReturn): time_return_analysis (dict of daily returns)
        # - SQN: sqn_analysis['sqn']

        # The user asked for CAGR, Win Rate, # of Trades, etc.:
        # # of Trades: From trade_analysis inside run_backtest we have total trades info.
        # We'll parse what we can from TradeAnalyzer here.
        trade_analysis = analyzer.trades.get_analysis()
        total_trades = trade_analysis.total.total if 'total' in trade_analysis and 'total' in trade_analysis.total else None
        won_trades = trade_analysis.won.total if 'won' in trade_analysis and 'total' in trade_analysis.won else None
        lost_trades = trade_analysis.lost.total if 'lost' in trade_analysis and 'total' in trade_analysis.lost else None
        win_rate = None
        if won_trades is not None and total_trades is not None and total_trades > 0:
            win_rate = (won_trades / total_trades) * 100.0

        # CAGR (not directly out-of-the-box), skip since user said if not out-of-box skip
        # Standard Deviation, Annualized Volatility, Sortino Ratio, Alpha, Information Ratio also skip.

        metrics = {
            'Final Portfolio Value': final_value,
            'Total Return': returns_analysis['rtot'],          # cumulative return
            'Total % Return': returns_analysis['rtot'] * 100,  # convert to percentage
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
        with sqlite3.connect('data/backtesting_results.db') as conn:
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

            # Retrieve the most recent backtest_id from backtest_summary
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
                # Optionally, handle the scenario where no backtest record exists
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
