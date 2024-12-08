# File: components/strategy_management_module/strategies/strategy_base.py
from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class StrategyBase(ABC):
    """Base class for all trading strategies."""

    def __init__(self, params: Dict):
        """
        Initialize strategy with parameters.
        
        Args:
            params: Strategy parameters
        """
        self.params = params
        self.validate_params()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals from market data.
        
        Args:
            data: Market data with OHLCV columns
            
        Returns:
            DataFrame with trading signals
        """
        pass

    @abstractmethod
    def validate_params(self) -> None:
        """
        Validate strategy parameters.
        
        Raises:
            ValueError: If parameters are invalid
        """
        pass
