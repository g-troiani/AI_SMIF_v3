# components/integration_communication_module/api_clients/zeromq_subscriber.py

import zmq
from ..config import Config
from ..logger import logger

class ZeroMQSubscriber:
    def __init__(self):
        self.context = zmq.Context()
        self.subscriber = self.context.socket(zmq.SUB)
        self.port = Config.ZEROMQ_PORT
        self.subscriber.connect(f"tcp://localhost:{self.port}")
        logger.info(f"ZeroMQ subscriber connected to port {self.port}.")

    def subscribe(self, topic):
        self.subscriber.setsockopt_string(zmq.SUBSCRIBE, topic)
        logger.debug(f"Subscribed to topic '{topic}'.")

    def receive(self):
        try:
            topic, message = self.subscriber.recv_multipart()
            logger.debug(f"Received message on topic '{topic.decode()}'.")
            return topic.decode(), message.decode()
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            raise

    def close(self):
        self.subscriber.close()
        self.context.term()
        logger.info("ZeroMQ subscriber closed.")
