from datetime import datetime
from components.backtesting_module.backtester import Backtester

if __name__ == "__main__":
    strategy_name = "BollingerBands"
    strategy_params = {
        'period': 20,
        'devfactor': 1.5
    }

    ticker = "SPY"
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 8)

    backtester = Backtester(
        strategy_name=strategy_name,
        strategy_params=strategy_params,
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
        stop_loss=2.0,       # Use desired stop loss percentage
        take_profit=5.0      # Use desired take profit percentage
    )

    backtester.run_backtest()

    metrics = backtester.get_performance_metrics()
    print("Backtest Metrics for Bollinger Bands on SPY:")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    benchmark_comparison = backtester.compare_with_benchmark("SPY")
    print("\nComparison with SPY Benchmark:")
    print("Strategy:", benchmark_comparison['Strategy'])
    print("Benchmark:", benchmark_comparison['Benchmark'])
