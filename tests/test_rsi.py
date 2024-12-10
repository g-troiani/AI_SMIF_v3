# test_rsi_strategy.py
from datetime import datetime
from components.backtesting_module.backtester import Backtester

if __name__ == "__main__":
    # Define the strategy name and parameters
    strategy_name = "RSI"
    strategy_params = {
        'rsi_period': 14,     # RSI period length
        'overbought': 70,     # RSI overbought threshold
        'oversold': 30        # RSI oversold threshold
    }

    # Define the ticker and date range for the test
    ticker = "SPY"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 8)

    # Initialize the backtester with optional stop_loss/take_profit
    backtester = Backtester(
        strategy_name=strategy_name,
        strategy_params=strategy_params,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        stop_loss=0.05,       # 5% stop loss (optional)
        take_profit=0.10      # 10% take profit (optional)
    )

    # Run the backtest
    backtester.run_backtest()

    # Retrieve and print performance metrics
    metrics = backtester.get_performance_metrics()
    print("Backtest Metrics for RSI Strategy on SPY:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    # Compare against the benchmark
    benchmark_comparison = backtester.compare_with_benchmark("SPY")
    print("\nComparison with SPY Benchmark:")
    print("Strategy:", benchmark_comparison['Strategy'])
    print("Benchmark:", benchmark_comparison['Benchmark'])
