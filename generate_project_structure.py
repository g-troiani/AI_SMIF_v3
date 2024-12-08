# File: generate_project_structure.py


import os
import pathlib
import logging
from typing import Dict, List, Union
from datetime import datetime

class ProjectStructureGenerator:
    """Creates a standardized project structure for a trading system MVP."""
    
    def __init__(self):
        # Configure logging
        self.setup_logging()
        
        # Define project structure
        self.root_dirs = [
            'config',
            'data',
            'logs',
            'components',
            'tests',
            'venv'
        ]
        
        self.components: Dict[str, Union[List, Dict]] = {
            'ui_module': {
                'dirs': {
                    'templates': [],
                    'static': ['css', 'js', 'images']
                },
                'files': ['app.py', 'routes.py', 'forms.py', 'socketio_events.py']
            },
            'data_management_module': {
                'dirs': {'database': []},
                'files': ['data_manager.py', 'data_access_layer.py', 'alpaca_api.py']
            },
            'strategy_management_module': {
                'dirs': {'strategies': []},
                'files': ['strategy_manager.py']
            },
            'backtesting_module': {
                'dirs': {'results': []},
                'files': ['backtester.py', 'optimizer.py']
            },
            'trading_execution_engine': {
                'dirs': {},
                'files': ['execution_engine.py', 'order_manager.py', 'alpaca_api.py']
            },
            'portfolio_management_module': {
                'dirs': {},
                'files': ['portfolio_manager.py', 'performance_metrics.py']
            },
            'risk_management_module': {
                'dirs': {},
                'files': ['risk_manager.py', 'stop_loss_handler.py', 'emergency_liquidation.py']
            },
            'reporting_analytics_module': {
                'dirs': {
                    'templates': [],
                    'static': ['css', 'js']
                },
                'files': ['report_generator.py', 'analytics.py']
            },
            'integration_communication_module': {
                'dirs': {'api_clients': []},
                'files': ['data_abstraction_layer.py', 'trade_abstraction_layer.py']
            },
            'logging_monitoring_module': {
                'dirs': {},
                'files': ['logger.py', 'monitoring.py', 'log_config.yaml']
            },
            'utils': {
                'dirs': {},
                'files': ['helpers.py', 'exceptions.py', 'decorators.py']
            }
        }
        
        self.root_files = {
            'README.md': self._get_readme_content(),
            'requirements.txt': self._get_requirements_content(),
            '.gitignore': self._get_gitignore_content()
        }

    def setup_logging(self) -> None:
        """Configure logging for the project structure generation."""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'project_structure_creation_{datetime.now():%Y%m%d_%H%M%S}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)

    def create_directory(self, path: str) -> None:
        """
        Create a directory and log the operation.
        
        Args:
            path: The directory path to create
        """
        try:
            os.makedirs(path, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
        except Exception as e:
            self.logger.error(f"Failed to create directory {path}: {str(e)}")
            raise

    def create_file(self, path: str, content: str = '') -> None:
        """
        Create a file with optional content and log the operation.
        
        Args:
            path: The file path to create
            content: Optional content to write to the file
        """
        try:
            with open(path, 'w') as f:
                f.write(content)
            self.logger.info(f"Created file: {path}")
        except Exception as e:
            self.logger.error(f"Failed to create file {path}: {str(e)}")
            raise

    def _get_readme_content(self) -> str:
        """Generate README.md content."""
        return """# Trading System MVP

## Overview
This is the MVP version of the trading system.

## Project Structure
- `config/`: Configuration files
- `data/`: Data storage
- `logs/`: Application logs
- `components/`: Main application modules
- `tests/`: Test suite
- `venv/`: Python virtual environment

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate virtual environment:
   - Windows: `venv\\Scripts\\activate`
   - Unix/MacOS: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`

## Components
- UI Module
- Data Management Module
- Strategy Management Module
- Backtesting Module
- Trading Execution Engine
- Portfolio Management Module
- Risk Management Module
- Reporting and Analytics Module
- Integration and Communication Module
- Logging and Monitoring Module
"""

    def _get_requirements_content(self) -> str:
        """Generate requirements.txt content."""
        return '\n'.join([''

        ])

    def _get_gitignore_content(self) -> str:
        """Generate .gitignore content."""
        return '\n'.join([
            '# Virtual Environment',
            'venv/',
            'env/',
            '.env',
            '',
            '# Python',
            '__pycache__/',
            '*.py[cod]',
            '*$py.class',
            '*.so',
            '',
            '# Logs',
            '*.log',
            'logs/',
            '',
            '# Database',
            '*.db',
            '*.sqlite3',
            '',
            '# Configuration',
            'config/*.ini',
            '',
            '# IDE',
            '.idea/',
            '.vscode/',
            '*.swp',
            '',
            '# OS',
            '.DS_Store',
            'Thumbs.db'
        ])

    def generate_structure(self) -> None:
        """Generate the complete project structure."""
        try:
            self.logger.info("Starting project structure generation")
            
            # Create root directories
            for dir_name in self.root_dirs:
                self.create_directory(dir_name)
            
            # Create component directories and files
            for component, config in self.components.items():
                component_path = os.path.join('components', component)
                self.create_directory(component_path)
                
                # Create __init__.py and config.py
                self.create_file(os.path.join(component_path, '__init__.py'))
                self.create_file(os.path.join(component_path, 'config.py'))
                
                # Create component directories
                for dir_name, subdirs in config['dirs'].items():
                    dir_path = os.path.join(component_path, dir_name)
                    self.create_directory(dir_path)
                    for subdir in subdirs:
                        self.create_directory(os.path.join(dir_path, subdir))
                
                # Create component files
                for file_name in config['files']:
                    self.create_file(os.path.join(component_path, file_name))
            
            # Create test files
            self.create_file(os.path.join('tests', '__init__.py'))
            for component in self.components:
                self.create_file(os.path.join('tests', f'test_{component}.py'))
            
            # Create root files
            for filename, content in self.root_files.items():
                self.create_file(filename, content)
            
            self.logger.info("Project structure generation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Project structure generation failed: {str(e)}")
            raise

if __name__ == '__main__':
    try:
        generator = ProjectStructureGenerator()
        generator.generate_structure()
        print("Project structure created successfully! Check the log file for details.")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Check the log file for more details.")