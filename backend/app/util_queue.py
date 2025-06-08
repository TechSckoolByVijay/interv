# file: util_queue.py
import uuid
import json
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from datetime import datetime

SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONNECTION_STR")
TOPIC_NAME = os.getenv("TOPIC_NAME")
SUBSCRIPTION_NAME = os.getenv("SUBSCRIPTION_NAME")


def send_message_to_service_bus(message: dict):
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=SERVICE_BUS_CONNECTION_STR)
    sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
    
    json_msg = json.dumps(message)
    service_bus_message = ServiceBusMessage(json_msg)
    
    with sender:
        sender.send_messages(service_bus_message)
