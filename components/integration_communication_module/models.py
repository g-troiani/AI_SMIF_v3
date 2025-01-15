# components/integration_communication_module/models.py

from dataclasses import dataclass

@dataclass
class MarketData:
    symbol: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class Order:
    id: str
    symbol: str
    qty: int
    side: str
    type: str
    time_in_force: str
    status: str
