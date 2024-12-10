# File: components/strategy_management_module/strategies/strategy_base.py
# Type: py

from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class StrategyBase(ABC):
    """Base class for all trading strategies."""

    def __init__(self, params: Dict):
        self.params = params
        self.validate_params()

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

    @abstractmethod
    def validate_params(self) -> None:
        pass
