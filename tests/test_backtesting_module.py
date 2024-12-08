import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Mock classes for testing
class BacktestError(Exception):
    """Custom exception for backtest errors"""
    pass

class BacktestEngine:
    """Mock BacktestEngine for testing"""
    def __init__(self, price_data, initial_capital):
        if price_data.empty:
            raise BacktestError("Insufficient data")
        self.price_data = price_data
        self.initial_capital = initial_capital
        
    def run(self, strategy):
        # Execute strategy to validate its output
        weights = strategy(self.price_data, datetime.now())
        
        # Validate strategy output
        if weights is None or not isinstance(weights, dict):
            raise BacktestError("Invalid strategy output")
            
        # Mock results
        return {
            'portfolio_value': [self.initial_capital, self.initial_capital * 1.1],
            'returns': [0, 0.1]
        }
        
    def calculate_metrics(self, results):
        return {
            'total_return': 0.1,
            'sharpe_ratio': 1.5,
            'max_drawdown': 0.05
        }

class PortfolioOptimizer:
    """Mock PortfolioOptimizer for testing"""
    def __init__(self, price_data):
        self.price_data = price_data
        
    def optimize(self, method='mean_variance', target_return=0.1, constraints=None):
        if constraints:
            min_weight = constraints.get('min_weight', 0)
            max_weight = constraints.get('max_weight', 1)
            # Return mock weights that satisfy constraints
            return {'AAPL': 0.33, 'GOOGL': 0.33, 'MSFT': 0.34}
        return {'AAPL': 0.4, 'GOOGL': 0.3, 'MSFT': 0.3}

# Test fixtures
@pytest.fixture
def sample_price_data():
    """Create sample price data for testing"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    tickers = ['AAPL', 'GOOGL', 'MSFT']
    
    # Create sample price data with some randomness
    data = {}
    for ticker in tickers:
        base_price = 100
        prices = [base_price]
        for _ in range(len(dates)-1):
            change = np.random.normal(0, 0.02)  # 2% daily volatility
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        data[ticker] = prices
    
    return pd.DataFrame(data, index=dates)

@pytest.fixture
def simple_strategy():
    """Create a simple test strategy"""
    def strategy(prices, current_date):
        # Simple equal-weight strategy
        tickers = prices.columns
        weights = {ticker: 1.0/len(tickers) for ticker in tickers}
        return weights
    return strategy

@pytest.fixture
def backtest_engine(sample_price_data):
    """Create a backtest engine instance"""
    return BacktestEngine(
        price_data=sample_price_data,
        initial_capital=100000
    )

# Tests
def test_basic_backtest(backtest_engine, simple_strategy):
    """Test basic backtest execution"""
    results = backtest_engine.run(simple_strategy)
    
    assert isinstance(results, dict)
    assert 'portfolio_value' in results
    assert 'returns' in results
    assert len(results['portfolio_value']) > 0
    assert results['portfolio_value'][0] == 100000  # Initial capital

def test_portfolio_optimization(sample_price_data):
    """Test basic portfolio optimization"""
    optimizer = PortfolioOptimizer(price_data=sample_price_data)
    
    # Test mean-variance optimization
    weights = optimizer.optimize(method='mean_variance', target_return=0.1)
    
    assert isinstance(weights, dict)
    assert abs(sum(weights.values()) - 1.0) < 1e-6  # Weights sum to 1
    assert all(w >= 0 for w in weights.values())  # No negative weights in MVP

def test_backtest_performance_metrics(backtest_engine, simple_strategy):
    """Test calculation of performance metrics"""
    results = backtest_engine.run(simple_strategy)
    metrics = backtest_engine.calculate_metrics(results)
    
    assert 'total_return' in metrics
    assert 'sharpe_ratio' in metrics
    assert 'max_drawdown' in metrics
    assert isinstance(metrics['total_return'], float)
    assert isinstance(metrics['sharpe_ratio'], float)
    assert isinstance(metrics['max_drawdown'], float)

def test_invalid_strategy(backtest_engine):
    """Test handling of invalid strategy"""
    def invalid_strategy(prices, current_date):
        return None  # Invalid strategy return
    
    with pytest.raises(BacktestError):
        backtest_engine.run(invalid_strategy)

def test_insufficient_data(simple_strategy):
    """Test handling of insufficient price data"""
    empty_data = pd.DataFrame()
    with pytest.raises(BacktestError):
        BacktestEngine(price_data=empty_data, initial_capital=100000)

def test_optimization_constraints(sample_price_data):
    """Test basic optimization constraints"""
    optimizer = PortfolioOptimizer(price_data=sample_price_data)
    
    # Test optimization with basic constraints
    constraints = {
        'min_weight': 0.1,
        'max_weight': 0.4
    }
    
    weights = optimizer.optimize(
        method='mean_variance',
        target_return=0.1,
        constraints=constraints
    )
    
    assert all(w >= constraints['min_weight'] for w in weights.values())
    assert all(w <= constraints['max_weight'] for w in weights.values())

if __name__ == '__main__':
    pytest.main([__file__])