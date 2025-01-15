# components/integration_communication_module/api_clients/zeromq_client.py

import zmq
from ..config import Config
from ..logger import logger

class ZeroMQClient:
    def __init__(self):
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.port = Config.ZEROMQ_PORT
        self.publisher.bind(f"tcp://*:{self.port}")
        logger.info(f"ZeroMQ publisher bound to port {self.port}.")

    def publish(self, topic, message):
        try:
            self.publisher.send_multipart([topic.encode(), message.encode()])
            logger.debug(f"Published message on topic '{topic}'.")
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            raise

    def close(self):
        self.publisher.close()
        self.context.term()
        logger.info("ZeroMQ publisher closed.")
