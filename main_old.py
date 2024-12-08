import logging
import sys
import signal
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from components.data_management_module.data_manager import DataManager
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,  # Changed from ERROR to INFO for better debugging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def verify_data(data_manager):
    """Verify data collection is working"""
    try:
        for ticker in data_manager.tickers:
            # Check last hour of data
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            data = data_manager.get_historical_data(ticker, start_time, end_time)
            if data is not None:
                logger.info(f"Recent data for {ticker}: {len(data)} records")
            else:
                logger.warning(f"No recent data found for {ticker}")
    except Exception as e:
        logger.error(f"Error verifying data: {str(e)}")

def setup_environment():
    """Setup necessary directories and files"""
    # Create directories
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    # Create tickers.csv if it doesn't exist
    tickers_file = Path('tickers.csv')
    if not tickers_file.exists():
        pd.DataFrame({'ticker': ['SPY']}).to_csv(tickers_file, index=False)  # Changed to just SPY as default
        logger.info("Created tickers.csv with default symbols")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal. Stopping application...")
    if data_manager:
        logger.info("Shutting down DataManager...")
        data_manager.shutdown()  # Using shutdown for proper cleanup
    sys.exit(0)

if __name__ == "__main__":
    logger.info("Starting market data collection system...")
    
    data_manager = None
    try:
        # Setup environment
        setup_environment()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize and start data manager
        logger.info("Initializing DataManager...")
        data_manager = DataManager()
        
        # Verify command socket is ready
        logger.info("Verifying command socket initialization...")
        if hasattr(data_manager, 'command_socket') and data_manager.command_thread.is_alive():
            logger.info("Command socket is ready")
        else:
            logger.error("Command socket failed to initialize properly")
            sys.exit(1)
        
        logger.info("Starting real-time data streaming...")
        data_manager.start_real_time_streaming()
        
        # Main loop
        while True:
            try:
                # Perform maintenance
                data_manager.perform_maintenance()
                
                # Verify data collection
                verify_data(data_manager)
                
                # Verify command thread is still running
                if not data_manager.command_thread.is_alive():
                    logger.error("Command thread has died, restarting...")
                    data_manager._setup_command_socket()
                
                # Wait before next check
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise
    finally:
        if data_manager:
            logger.info("Shutting down DataManager...")
            data_manager.shutdown()  # Using shutdown for proper cleanup
















# import logging
# import sys
# import signal
# from datetime import datetime, timedelta
# import pandas as pd
# from pathlib import Path
# from components.data_management_module.data_manager import DataManager
# import time

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('logs/data_manager.log'),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)

# def verify_data(data_manager):
#     """Verify data collection is working"""
#     try:
#         for ticker in data_manager.tickers:
#             # Check last hour of data
#             end_time = datetime.now()
#             start_time = end_time - timedelta(hours=1)
            
#             data = data_manager.get_historical_data(ticker, start_time, end_time)
#             if data is not None:
#                 logger.info(f"Recent data for {ticker}: {len(data)} records")
#             else:
#                 logger.warning(f"No recent data found for {ticker}")
#     except Exception as e:
#         logger.error(f"Error verifying data: {str(e)}")

# def setup_environment():
#     """Setup necessary directories and files"""
#     # Create directories
#     Path('data').mkdir(exist_ok=True)
#     Path('logs').mkdir(exist_ok=True)
    
#     # Create tickers.csv if it doesn't exist
#     tickers_file = Path('tickers.csv')
#     if not tickers_file.exists():
#         pd.DataFrame({'ticker': ['AAPL', 'MSFT', 'GOOGL']}).to_csv(tickers_file, index=False)
#         logger.info("Created tickers.csv with default symbols")

# def signal_handler(signum, frame):
#     """Handle shutdown signals"""
#     logger.info("Received shutdown signal. Stopping application...")
#     if data_manager:
#         data_manager.stop_real_time_streaming()
#     sys.exit(0)

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.ERROR)
#     logger = logging.getLogger(__name__)
#     logger.info("Initializing DataManager...")
    
#     data_manager = None
#     try:
#         # Setup environment
#         setup_environment()
        
#         # Register signal handlers
#         signal.signal(signal.SIGINT, signal_handler)
#         signal.signal(signal.SIGTERM, signal_handler)
        
#         # Initialize and start data manager
#         logger.info("Initializing DataManager...")
#         data_manager = DataManager()
        
#         logger.info("Starting real-time data streaming...")
#         data_manager.start_real_time_streaming()
        
#         # Main loop
#         while True:
#             try:
#                 # Perform maintenance
#                 data_manager.perform_maintenance()
                
#                 # Verify data collection
#                 verify_data(data_manager)
                
#                 # Wait before next check
#                 time.sleep(300)  # Check every 5 minutes
                
#             except Exception as e:
#                 logger.error(f"Error in main loop: {str(e)}")
#                 time.sleep(60)  # Wait a minute before retrying
                
#     except Exception as e:
#         logger.error(f"Fatal error in main: {str(e)}")
#         raise
#     finally:
#         if data_manager:
#             data_manager.stop_real_time_streaming() 