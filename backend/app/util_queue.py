# file: util_queue.py
import uuid
import json
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from datetime import datetime
import os
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from typing import Union
import logging

SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONNECTION_STR")
TOPIC_NAME = os.getenv("TOPIC_NAME")
SUBSCRIPTION_NAME = os.getenv("SUBSCRIPTION_NAME")

logger = logging.getLogger("servicebus")
logger.setLevel(logging.INFO)

class FileProcessPayload(BaseModel):
    docPath: str
    fileType: str

class QuestionProcessPayload(BaseModel):
    interview_id: int
    question_id: int

ServiceBusMessagePayload = Union[FileProcessPayload, QuestionProcessPayload]

class ServiceBusMessageModel(BaseModel):
    correlationId: str
    session_id: str
    action_type: str
    user_id: int
    timestamp: str
    status: str
    payload: ServiceBusMessagePayload

def send_message_to_service_bus(message: dict):
    logger.info("Preparing to send message to Azure Service Bus.")
    try:
        servicebus_client = ServiceBusClient.from_connection_string(conn_str=SERVICE_BUS_CONNECTION_STR)
        logger.debug("ServiceBusClient created.")
        sender = servicebus_client.get_topic_sender(topic_name=TOPIC_NAME)
        logger.debug(f"Topic sender created for topic: {TOPIC_NAME}")
        
        json_msg = json.dumps(message)
        logger.debug(f"Message serialized to JSON: {json_msg}")
        service_bus_message = ServiceBusMessage(json_msg)  # This is Azure's ServiceBusMessage
        
        with sender:
            sender.send_messages(service_bus_message)
            logger.info("Message sent to Azure Service Bus successfully.")
    except Exception as e:
        logger.error(f"Failed to send message to Azure Service Bus: {e}")