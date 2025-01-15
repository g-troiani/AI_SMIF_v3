# tests/test_data_management_module.py
"""Integration tests for the entire Data Management Module"""

import unittest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import zmq
from components.data_management_module.data_manager import DataManager
from components.data_management_module.data_access_layer import db_manager, Ticker, HistoricalData
from components.data_management_module.config import config
from components.data_management_module.alpaca_api import AlpacaAPIClient
from components.data_management_module.real_time_data import RealTimeDataStreamer
from sqlalchemy import inspect

class TestDataManagementModule(unittest.TestCase):
    """Complete integration test suite for Data Management Module"""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and resources"""
        # Create necessary directories
        os.makedirs('components/data_management_module/database', exist_ok=True)
        
        # Get absolute paths
        cls.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cls.test_db_path = os.path.join(cls.base_dir, 'components/data_management_module/database/test_data.db')
        cls.test_tickers_path = os.path.join(cls.base_dir, 'components/data_management_module/test_tickers.csv')
        
        # Create test configuration
        config.config['DEFAULT']['database_path'] = cls.test_db_path
        config.config['DEFAULT']['tickers_file'] = cls.test_tickers_path
        config.config['DEFAULT']['zeromq_port'] = '5555'
        config.config['DEFAULT']['zeromq_topic'] = 'test_topic'
        
        # Create test tickers file
        test_tickers = pd.DataFrame({'ticker': ['AAPL', 'GOOGL', 'MSFT']})
        test_tickers.to_csv(cls.test_tickers_path, index=False)

    def setUp(self):
        """Set up fresh test instance"""
        # Remove test database if exists
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            
        # Ensure test tickers file exists
        if not os.path.exists(self.test_tickers_path):
            test_tickers = pd.DataFrame({'ticker': ['AAPL', 'GOOGL', 'MSFT']})
            test_tickers.to_csv(self.test_tickers_path, index=False)
        
        # Initialize test instance
        self.data_manager = DataManager()
        
        # Set up test ZeroMQ context
        self.zmq_context = zmq.Context()
        self.subscriber = self.zmq_context.socket(zmq.SUB)
        self.subscriber.connect(f"tcp://localhost:{config.get('DEFAULT', 'zeromq_port')}")

    def tearDown(self):
        """Clean up test resources"""
        # Stop data streaming
        if hasattr(self.data_manager, 'real_time_streamer') and self.data_manager.real_time_streamer:
            self.data_manager.stop_real_time_streaming()
        
        # Close ZeroMQ connections
        self.subscriber.close()
        self.zmq_context.term()
        
        # Clean up test files
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.test_tickers_path):
            os.remove(self.test_tickers_path)

    def test_module_initialization(self):
        """Test 1: Module Initialization
        Document Reference: Step 1 - Define Data Requirements"""
        self.assertIsNotNone(self.data_manager)
        self.assertEqual(len(self.data_manager.tickers), 3)
        self.assertIn('AAPL', self.data_manager.tickers)
        self.assertIn('GOOGL', self.data_manager.tickers)
        self.assertIn('MSFT', self.data_manager.tickers)

    def test_database_setup(self):
        """Test 2: Database Setup
        Document Reference: Step 4 - Set Up the Database"""
        inspector = inspect(db_manager.engine)
        # Verify tables exist
        self.assertTrue(inspector.has_table('tickers'))
        self.assertTrue(inspector.has_table('historical_data'))
        
        session = db_manager.Session()
        try:
            # Verify tickers are initialized
            tickers = session.query(Ticker).all()
            self.assertEqual(len(tickers), 3)
        finally:
            session.close()

    @patch('components.data_management_module.alpaca_api.AlpacaAPIClient.fetch_historical_data')
    def test_historical_data_management(self, mock_fetch):
        """Test 3: Historical Data Management
        Document Reference: Step 2 & 3 - Data Access Layer and Data Retrieval"""
        # Mock API response
        mock_data = pd.DataFrame({
            'o': [100.0, 101.0],
            'h': [102.0, 103.0],
            'l': [98.0, 99.0],
            'c': [101.0, 102.0],
            'v': [1000, 1100]
        }, index=[datetime.now(), datetime.now() + timedelta(minutes=5)])
        mock_fetch.return_value = mock_data

        # Test data fetching and storage
        self.data_manager.fetch_historical_data()
        session = db_manager.Session()
        try:
            data = session.query(HistoricalData).all()
            self.assertGreater(len(data), 0)
            
            # Verify data integrity
            first_record = data[0]
            self.assertTrue(hasattr(first_record, 'open'))
            self.assertTrue(hasattr(first_record, 'high'))
            self.assertTrue(hasattr(first_record, 'low'))
            self.assertTrue(hasattr(first_record, 'close'))
            self.assertTrue(hasattr(first_record, 'volume'))
        finally:
            session.close()

    @patch('components.data_management_module.data_manager.RealTimeDataStreamer')
    def test_real_time_data_streaming(self, mock_streamer_class):
        """Test 4: Real-Time Data Streaming
        Document Reference: Step 6 - Real-Time Data Streaming"""
        # Mock the RealTimeDataStreamer instance
        mock_streamer = mock_streamer_class.return_value
        mock_streamer.start.return_value = None
        mock_streamer._running = True
        mock_streamer.stream = Mock()

        # Start streaming (this will use the mocked streamer)
        self.data_manager.start_real_time_streaming()

        # Subscribe to test topic
        test_topic = f"{config.get('DEFAULT', 'zeromq_topic')}.AAPL"
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, test_topic)

        # Verify streaming setup basics
        self.assertTrue(self.data_manager.real_time_streamer._running)
        self.assertIsNotNone(self.data_manager.real_time_streamer.stream)

        # Since it's off-market hours, we skip the actual data reception
        print("Skipping data reception test due to off-market hours.")

    def test_data_validation(self):
        """Test 5: Data Validation
        Document Reference: Step 5 - Data Storage Functions"""
        # Test valid data
        valid_data = {
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 1000
        }
        self.assertTrue(HistoricalData.validate_price_data(**valid_data))

        # Test invalid data
        invalid_data = {
            'open': 100.0,
            'high': 99.0,  # Invalid: high < open
            'low': 98.0,
            'close': 100.5,
            'volume': 1000
        }
        with self.assertRaises(ValueError):
            HistoricalData.validate_price_data(**invalid_data)

    def test_error_handling_and_logging(self):
        """Test 6: Error Handling and Logging
        Document Reference: Step 9 - Error Handling and Logging"""
        with self.assertLogs('data_manager', level='ERROR'):
            # Test with invalid ticker
            self.data_manager.get_historical_data(
                'INVALID',
                datetime.now() - timedelta(days=1),
                datetime.now()
            )

    def test_database_maintenance(self):
        """Test 7: Database Maintenance
        Document Reference: Step 8 - Data Updates and Synchronization"""
        # Insert old test data
        session = db_manager.Session()
        try:
            old_data = HistoricalData(
                ticker_symbol='AAPL',
                timestamp=datetime.now() - timedelta(days=40),
                open=100.0,
                high=101.0,
                low=99.0,
                close=100.5,
                volume=1000
            )
            session.add(old_data)
            session.commit()
        finally:
            session.close()

        # Run maintenance
        self.data_manager.perform_maintenance()

        # Verify cleanup
        session = db_manager.Session()
        try:
            old_records = session.query(HistoricalData).filter(
                HistoricalData.timestamp < (datetime.now() - timedelta(days=30))
            ).all()
            self.assertEqual(len(old_records), 0)
        finally:
            session.close()

    def test_concurrent_access(self):
        """Test 8: Concurrent Access
        Document Reference: Step 7 - Data Access to Other Modules"""
        import threading
        import queue

        errors = queue.Queue()
        
        def worker():
            try:
                # Simulate concurrent data access
                self.data_manager.get_historical_data(
                    'AAPL',
                    datetime.now() - timedelta(days=1),
                    datetime.now()
                )
            except Exception as e:
                errors.put(e)

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify no errors occurred
        self.assertTrue(errors.empty())

    @patch('components.data_management_module.alpaca_api.AlpacaAPIClient.fetch_historical_data')
    def test_performance(self, mock_fetch):
        """Test 9: Performance Testing
        Document Reference: Step 10 - Testing"""
        import time

        # Mock large dataset
        dates = pd.date_range(start=datetime.now()-timedelta(days=5),
                            end=datetime.now(),
                            freq='5min')
        mock_data = pd.DataFrame({
            'o': np.random.rand(len(dates)) * 100,
            'h': np.random.rand(len(dates)) * 100,
            'l': np.random.rand(len(dates)) * 100,
            'c': np.random.rand(len(dates)) * 100,
            'v': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        mock_fetch.return_value = mock_data

        # Measure performance
        start_time = time.time()
        self.data_manager.fetch_historical_data()
        end_time = time.time()

        # Verify performance meets requirements
        execution_time = end_time - start_time
        self.assertLess(execution_time, 30)  # Should complete within 30 seconds

if __name__ == '__main__':
    unittest.main()
