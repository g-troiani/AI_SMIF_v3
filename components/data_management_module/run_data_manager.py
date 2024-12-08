import logging
from components.data_management_module.data_manager import DataManager
import time
import signal
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    logger.info("Received shutdown signal. Stopping application...")
    if data_manager:
        data_manager.stop_real_time_streaming()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    data_manager = None
    try:
        logger.info("Initializing DataManager...")
        data_manager = DataManager()
        
        # Start real-time streaming
        logger.info("Starting real-time data streaming...")
        data_manager.start_real_time_streaming()
        
        # Keep the script running and perform maintenance
        while True:
            try:
                # Perform maintenance every 24 hours
                data_manager.perform_maintenance()
                
                # Verify data is being collected
                for ticker in data_manager.tickers:
                    latest_data = data_manager.get_historical_data(
                        ticker,
                        start_date=datetime.now() - timedelta(hours=1),
                        end_date=datetime.now()
                    )
                    if latest_data:
                        logger.info(f"Latest data for {ticker}: {len(latest_data)} records")
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise
    finally:
        if data_manager:
            data_manager.stop_real_time_streaming()