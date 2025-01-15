# components/live_trading_module/zeromq_price_streamer.py

import zmq
import json
import logging
from datetime import datetime
import pytz
import time

class ZeroMQPriceStreamer:
    """
    Sprint 3:
    Subscribes to the ZeroMQ publisher from real_time_data.py.
    This acts as fallback if AlpacaStoreStreamer fails.
    """

    def __init__(self, topic, port):
        self.logger = logging.getLogger("ZeroMQPriceStreamer")
        self.topic = topic
        self.port = port
        self.zmq_context = zmq.Context()
        self.subscriber = self.zmq_context.socket(zmq.SUB)
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, self.topic)
        connect_str = f"tcp://localhost:{self.port}"
        self.subscriber.connect(connect_str)
        self._running = False

    def start(self, callback):
        """
        callback: a function to call with received data
        callback signature: callback(symbol, timestamp, open, high, low, close, volume)
        """
        self._running = True
        self.logger.info("ZeroMQPriceStreamer started")
        while self._running:
            try:
                msg = self.subscriber.recv_string(flags=zmq.NOBLOCK)
                if msg:
                    # msg format: "topic {json}"
                    # example: "market_data.AAPL { ... }"
                    parts = msg.split(' ', 1)
                    if len(parts) == 2:
                        # parse json
                        data = json.loads(parts[1])
                        symbol = data['symbol']
                        ts = datetime.fromisoformat(data['timestamp'])
                        o = data['open']
                        h = data['high']
                        l = data['low']
                        c = data['close']
                        v = data['volume']
                        callback(symbol, ts, o, h, l, c, v)
            except zmq.Again:
                # no message yet
                time.sleep(0.5)
            except Exception as e:
                self.logger.error(f"Error in ZeroMQPriceStreamer: {str(e)}")
                time.sleep(1)

    def stop(self):
        self._running = False
        self.subscriber.close()
        self.zmq_context.term()
        self.logger.info("ZeroMQPriceStreamer stopped")
