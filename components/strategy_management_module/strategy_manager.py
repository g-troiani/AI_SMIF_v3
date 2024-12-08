# File: components/strategy_management_module/strategy_manager.py

import importlib
import os
import json
import logging
from typing import Dict, List, Optional

class StrategyManager:
    """Manages trading strategy configurations and lifecycle."""
    
    # Strategy class mapping
    STRATEGY_CLASS_MAPPING = {
        'moving_average_crossover': 'MovingAverageCrossover',
        'rsi_strategy': 'RSIStrategy',  # This was wrong - correct case
        'macd_strategy': 'MACDStrategy',  # This was wrong - correct case
        'bollinger_bands_strategy': 'BollingerBandsStrategy',
        'momentum_strategy': 'MomentumStrategy'
    }

    def __init__(self, config_file: str = 'config/strategies.json'):
        """
        Initialize the StrategyManager.
        
        Args:
            config_file: Path to the strategies configuration file
        """
        self.config_file = config_file
        self.strategies = {}
        self.logger = logging.getLogger(__name__)
        self.load_strategies()

    def load_strategies(self) -> None:
        """Load strategies from the configuration file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    strategies_config = json.load(f)
                    for strategy_name, params in strategies_config.items():
                        self.add_strategy(strategy_name, params)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading strategies: {e}")

    def save_strategies(self) -> None:
        """Save current strategy configurations to file."""
        try:
            strategies_config = {name: strategy.params 
                               for name, strategy in self.strategies.items()}
            with open(self.config_file, 'w') as f:
                json.dump(strategies_config, f, indent=4)
        except IOError as e:
            self.logger.error(f"Error saving strategies: {e}")

    def add_strategy(self, strategy_name: str, params: dict) -> bool:
        """
        Add a new strategy.
        
        Args:
            strategy_name: Name of the strategy
            params: Strategy parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            module_name = f"components.strategy_management_module.strategies.{strategy_name}"
            module = importlib.import_module(module_name)
            
            # Special handling for known acronyms
            known_acronyms = {'rsi': 'RSI', 'macd': 'MACD'}
            
            # Split the strategy name and process each part
            parts = strategy_name.replace('_strategy', '').split('_')
            processed_parts = []
            
            for part in parts:
                if part.lower() in known_acronyms:
                    processed_parts.append(known_acronyms[part.lower()])
                else:
                    processed_parts.append(part.title())
                    
            class_name = ''.join(processed_parts) + 'Strategy'
            
            strategy_class = getattr(module, class_name)
            strategy_instance = strategy_class(params)
            self.strategies[strategy_name] = strategy_instance
            self.save_strategies()
            return True
        except Exception as e:
            self.logger.error(f"Error adding strategy '{strategy_name}': {e}")
            return False

    def remove_strategy(self, strategy_name: str) -> bool:
        """
        Remove a strategy.
        
        Args:
            strategy_name: Name of the strategy to remove
        
        Returns:
            bool: True if successful, False otherwise
        """
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            self.save_strategies()
            return True
        return False

    def get_strategy(self, strategy_name: str):
        """
        Get a strategy instance.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Strategy instance or None
        """
        return self.strategies.get(strategy_name)

    def list_strategies(self) -> List[str]:
        """
        Get list of all available strategies.
        
        Returns:
            List of strategy names
        """
        return list(self.strategies.keys())

    def get_strategy_params(self, strategy_name: str) -> Optional[Dict]:
        """
        Get parameters for a specific strategy.
        
        Args:
            strategy_name: Name of the strategy
            
        Returns:
            Dictionary of parameters or None
        """
        strategy = self.get_strategy(strategy_name)
        return strategy.params if strategy else None