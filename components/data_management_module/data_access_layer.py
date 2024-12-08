# components/data_management_module/data_access_layer.py

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, UniqueConstraint, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, timedelta
import logging
from .config import config

Base = declarative_base()

class Ticker(Base):
    __tablename__ = 'tickers'
    symbol = Column(String, primary_key=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    added_date = Column(DateTime, default=datetime.utcnow)

class HistoricalData(Base):
    __tablename__ = 'historical_data'
    id = Column(Integer, primary_key=True)
    ticker_symbol = Column(String, ForeignKey('tickers.symbol'))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    # Ensure we don't have duplicate data points
    __table_args__ = (UniqueConstraint('ticker_symbol', 'timestamp'),)

    @staticmethod
    def validate_price_data(open, high, low, close, volume):
        """Validate price data before insertion"""
        if not all(isinstance(x, (int, float)) for x in [open, high, low, close, volume]):
            raise ValueError("All price and volume data must be numeric")
        if not (high >= max(open, close) and low <= min(open, close)):
            raise ValueError("High/low prices are inconsistent with open/close prices")
        if volume < 0:
            raise ValueError("Volume cannot be negative")
        return True

class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(
            f"sqlite:///{config.get('DEFAULT', 'database_path')}",
            connect_args={'check_same_thread': False, 'timeout': 15}  # Added parameters
        )
        # Optionally set journal mode to WAL to improve concurrency
        with self.engine.connect() as conn:
            conn.execute(text('PRAGMA journal_mode=WAL;'))
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._setup_logging()

    def _setup_logging(self):
        self.logger = logging.getLogger('database_manager')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(config.get('DEFAULT', 'log_file'))
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def add_ticker(self, symbol):
        """Add a new ticker to the database"""
        session = self.Session()
        try:
            ticker = Ticker(symbol=symbol)
            session.add(ticker)
            session.commit()
            self.logger.info(f"Added new ticker: {symbol}")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error adding ticker {symbol}: {str(e)}")
            raise
        finally:
            session.close()

    def bulk_insert_historical_data(self, records):
        """Insert multiple historical data records"""
        session = self.Session()
        try:
            session.bulk_save_objects(records)
            session.commit()
            self.logger.info(f"Bulk inserted {len(records)} records")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error in bulk insert: {str(e)}")
            raise
        finally:
            session.close()

    def get_historical_data(self, ticker, start_date, end_date):
        """Retrieve historical data for a specific ticker and date range"""
        session = self.Session()
        try:
            query = session.query(HistoricalData).filter(
                HistoricalData.ticker_symbol == ticker,
                HistoricalData.timestamp.between(start_date, end_date)
            ).order_by(HistoricalData.timestamp)
            return query.all()
        finally:
            session.close()

    def cleanup_old_data(self, days_to_keep=30):
        """Cleanup historical data older than specified days"""
        session = self.Session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            deleted = session.query(HistoricalData).filter(
                HistoricalData.timestamp < cutoff_date
            ).delete()
            session.commit()
            if deleted > 0:
                session.execute(text('VACUUM'))  # Defragment the database
            self.logger.info(f"Cleaned up {deleted} old records")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error during cleanup: {str(e)}")
            raise
        finally:
            session.close()

    def create_session(self):
        """Create and return a new database session"""
        try:
            session = self.Session()
            return session
        except Exception as e:
            self.logger.error(f"Error creating database session: {str(e)}")
            raise
        
    def save_real_time_data(self, bar):
        """Save real-time streamed data as appended records to the database"""
        session = self.Session()
        try:
            # Validate the data
            HistoricalData.validate_price_data(
                bar.open, bar.high, bar.low, bar.close, bar.volume
            )

            # Create a new HistoricalData record
            data = HistoricalData(
                ticker_symbol=bar.symbol,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume
            )

            # Add and commit the new record
            session.add(data)
            session.commit()
            self.logger.info(f"Appended real-time data for {bar.symbol} at {bar.timestamp} to the database")
        except IntegrityError as ie:
            session.rollback()
            self.logger.warning(f"Data for {bar.symbol} at {bar.timestamp} already exists in the database.")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error saving real-time data: {str(e)}")
            raise
        finally:
            session.close()
            
    def get_last_timestamp(self, ticker_symbol):
        """Get the timestamp of the last record for a ticker in the database."""
        session = self.Session()
        try:
            last_record = session.query(HistoricalData.timestamp)\
                .filter(HistoricalData.ticker_symbol == ticker_symbol)\
                .order_by(HistoricalData.timestamp.desc())\
                .first()
            if last_record:
                return last_record[0]
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting last timestamp for {ticker_symbol}: {str(e)}")
            raise
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()
