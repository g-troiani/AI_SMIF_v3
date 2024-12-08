# tests/test_zeromq.py

import threading
import time
from components.integration_communication_module.api_clients.zeromq_client import ZeroMQClient
from components.integration_communication_module.api_clients.zeromq_subscriber import ZeroMQSubscriber

def publisher_thread():
    publisher = ZeroMQClient()
    for i in range(5):
        publisher.publish('test_topic', f'Message {i}')
        time.sleep(1)
    publisher.close()

def subscriber_thread():
    subscriber = ZeroMQSubscriber()
    subscriber.subscribe('test_topic')
    for _ in range(5):
        topic, message = subscriber.receive()
        print(f"Received: {topic} - {message}")
    subscriber.close()

if __name__ == '__main__':
    t1 = threading.Thread(target=publisher_thread)
    t2 = threading.Thread(target=subscriber_thread)
    t2.start()
    t1.start()
    t1.join()
    t2.join()
