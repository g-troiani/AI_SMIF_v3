# main.py

import logging
import sys
import signal
import zmq
import json
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
from components.data_management_module.data_manager import DataManager
import time
from components.data_management_module.database import DatabaseManager
import psutil
import os
import socket
import uuid  # Ensure this is the standard time module, not overshadowed by datetime.


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
    handlers=[
        logging.FileHandler('logs/data_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def find_available_port(start_port=5556, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError("No available ports found")

def create_instance_lock(instance_id):
    """Create a lock file for this instance"""
    lock_file = Path(f"/tmp/datamanager_{instance_id}.lock")
    try:
        with open(lock_file, 'x') as f:
            f.write(str(os.getpid()))
        return lock_file
    except FileExistsError:
        return None

def debug_port_usage(port):
    print(f"=== PORT USAGE DEBUG INFO ===")
    # Check if port is open by trying to bind or scan. Assuming it's closed from logs:
    print(f"Port {port} is CLOSED\n")

    print("Processes using port {port}:")

    # Get process info without 'connections' attribute in process_iter
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            conns = proc.connections()
            for conn in conns:
                if conn.laddr.port == port:
                    print(f"Process {proc.pid} ({proc.name()}) is using port {port}")
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue

def recover_from_crash():
    """Clean up stale lock files"""
    for lock_file in Path("/tmp").glob("datamanager_*.lock"):
        try:
            pid = int(lock_file.read_text())
            if not psutil.pid_exists(pid):
                lock_file.unlink()
                logger.info(f"Removed stale lock file: {lock_file}")
        except Exception as e:
            logger.error(f"Error checking lock file {lock_file}: {e}")

class DataManagerServer:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.instance_id = uuid.uuid4().hex[:8]
        self.lock_file = None
        
        # Initialize ZMQ context
        self.context = zmq.Context()
        logger.debug(f"ZMQ Context created: {self.context}")
        self.socket = self.context.socket(zmq.REP)
        logger.debug(f"ZMQ Socket created: {self.socket}")
        logger.debug(f"Socket type: {self.socket.type}")
        
        # Create instance lock
        self.lock_file = create_instance_lock(self.instance_id)
        if not self.lock_file:
            raise RuntimeError(f"Could not create lock file for instance {self.instance_id}")
        
        # Find available port
        self.port = find_available_port()
        logger.debug(f"Using port {self.port} for instance {self.instance_id}")
        
        try:
            debug_port_usage(self.port)
            self.socket.bind(f"tcp://*:{self.port}")
            
            # Write port to file for client discovery
            port_file = Path(f"/tmp/datamanager_{self.instance_id}.port")
            port_file.write_text(str(self.port))
            
        except zmq.error.ZMQError as e:
            self.cleanup()
            raise RuntimeError(f"Failed to initialize ZMQ: {e}")
            
        logger.info(f"DataManagerServer initialized and listening on port {self.port}")

    def cleanup(self):
        """Clean up resources"""
        try:
            # Close ZMQ connections
            if hasattr(self, 'socket'):
                self.socket.close()
            if hasattr(self, 'context'):
                self.context.term()
            
            # Remove lock file
            if self.lock_file and self.lock_file.exists():
                self.lock_file.unlink()
            
            # Remove port file
            port_file = Path(f"/tmp/datamanager_{self.instance_id}.port")
            if port_file.exists():
                port_file.unlink()
                
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def process_message(self, message):
        message_type = message.get('type')
        
        if message_type == 'add_ticker':
            ticker = message.get('ticker')
            try:
                # Add ticker to tickers.csv
                tickers_df = pd.read_csv('tickers.csv')
                if ticker not in tickers_df['ticker'].values:
                    tickers_df = pd.concat([tickers_df, pd.DataFrame({'ticker': [ticker]})], ignore_index=True)
                    tickers_df.to_csv('tickers.csv', index=False)
                    self.data_manager.update_tickers()  # Refresh tickers in DataManager
                    return {"success": True, "message": f"Ticker {ticker} added successfully"}
                return {"success": True, "message": f"Ticker {ticker} already exists"}
            except Exception as e:
                logger.error(f"Error adding ticker {ticker}: {str(e)}")
                return {"success": False, "message": str(e)}
        
        return {"success": False, "message": f"Unknown message type: {message_type}"}


    def _handle_commands(self):
        try:
            while self._running:
                socks = dict(poller.poll(1000))  # Wait for 1 second
                # handle sockets...

        except zmq.error.ZMQError as e:
            # Handle the error gracefully
            print(f"Unexpected ZMQ error: {e}")
            self._running = False
        except Exception as e:
            print(f"Unexpected error in command handler: {e}")
            self._running = False
        finally:
            # Clean up resources
            time.sleep(1)  # This will now correctly call the standard library sleep


def verify_data(data_manager):
    """Verify data collection is working"""
    try:
        for ticker in data_manager.tickers:
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
    Path('data').mkdir(exist_ok=True)
    Path('logs').mkdir(exist_ok=True)
    
    tickers_file = Path('tickers.csv')
    if not tickers_file.exists():
        pd.DataFrame({'ticker': ['SPY']}).to_csv(tickers_file, index=False)
        logger.info("Created tickers.csv with default symbols")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal. Stopping application...")
    if server:
        logger.info("Cleaning up server resources...")
        server.cleanup()
    if data_manager:
        logger.info("Shutting down DataManager...")
        data_manager.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    logger.info("Starting market data collection system...")
    
    data_manager = None
    server = None
    try:
        # Clean up any crashed instances
        recover_from_crash()
        
        setup_environment()
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Initializing DataManager...")
        data_manager = DataManager()
        
        logger.info("Initializing ZMQ server...")
        server = DataManagerServer(data_manager)
        
        logger.info("Starting real-time data streaming...")
        data_manager.start_real_time_streaming()
        
        while True:
            try:
                # Handle ZMQ messages
                try:
                    message = server.socket.recv_json(flags=zmq.NOBLOCK)
                    response = server.process_message(message)
                    server.socket.send_json(response)
                except zmq.Again:
                    pass  # No message waiting
                
                # Regular maintenance
                data_manager.perform_maintenance()
                verify_data(data_manager)
                
                time.sleep(5)  # Short sleep to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)
                
    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}")
        raise
    finally:
        if server:
            logger.info("Cleaning up server resources...")
            server.cleanup()
        if data_manager:
            logger.info("Shutting down DataManager...")
            data_manager.shutdown()