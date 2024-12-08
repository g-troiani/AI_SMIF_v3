# File: components/trading_execution_engine/trade_signal.py
# Type: py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TradeSignal:
    """
    Represents a standardized trade signal with support for different order types.
    """
    ticker: str
    signal_type: str  # 'BUY' or 'SELL'
    quantity: float
    strategy_id: str
    timestamp: datetime
    price: Optional[float] = None  # Market price for reference
    order_type: str = 'market'  # 'market', 'limit', or 'stop'
    limit_price: Optional[float] = None  # Price for limit orders
    stop_price: Optional[float] = None  # Price for stop orders
    time_in_force: str = 'gtc'  # 'day', 'gtc', 'opg', 'cls', 'ioc', 'fok'

    def __post_init__(self):
        # Basic validation
        if self.signal_type not in ('BUY', 'SELL'):
            raise ValueError("signal_type must be 'BUY' or 'SELL'.")

        if self.order_type not in ('market', 'limit', 'stop'):
            raise ValueError("order_type must be 'market', 'limit', or 'stop'.")

        if self.time_in_force not in ('day', 'gtc', 'opg', 'cls', 'ioc', 'fok'):
            raise ValueError("Invalid time_in_force value.")

        # Validate limit and stop prices based on order type
        if self.order_type == 'limit' and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders.")

        if self.order_type == 'stop' and self.stop_price is None:
            raise ValueError("stop_price is required for stop orders.")

    def to_dict(self) -> dict:
        """
        Serializes the TradeSignal to a dictionary.
        """
        return {
            'ticker': self.ticker,
            'signal_type': self.signal_type,
            'quantity': self.quantity,
            'strategy_id': self.strategy_id,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'order_type': self.order_type,
            'limit_price': self.limit_price,
            'stop_price': self.stop_price,
            'time_in_force': self.time_in_force
        }

    @staticmethod
    def from_dict(data: dict) -> 'TradeSignal':
        """
        Deserializes a dictionary to a TradeSignal object.
        """
        required_fields = ['ticker', 'signal_type', 'quantity', 'strategy_id', 'timestamp']
        for field in required_fields:
            if field not in data:
                raise KeyError(f"Missing required field '{field}' in trade signal data.")
        return TradeSignal(
            ticker=data['ticker'],
            signal_type=data['signal_type'],
            quantity=float(data['quantity']),
            strategy_id=data['strategy_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            price=float(data['price']) if 'price' in data and data['price'] is not None else None,
            order_type=data.get('order_type', 'market'),
            limit_price=float(data['limit_price']) if 'limit_price' in data and data['limit_price'] is not None else None,
            stop_price=float(data['stop_price']) if 'stop_price' in data and data['stop_price'] is not None else None,
            time_in_force=data.get('time_in_force', 'gtc')
        )
