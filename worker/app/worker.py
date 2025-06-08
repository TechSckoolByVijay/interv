# worker/app/worker.py
import json
from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode

#from db import Session, Interview
from shared.models import Interview, QuestionAnswer
from shared.database import SessionLocal
from worker.app.langchain_chat import generate_next_question
from dotenv import load_dotenv
#from worker.app.langgraph_interview import graph
import os
#from shared.models import Interview, QuestionAnswer
from shared.logger import logger




load_dotenv()  # Load environment variables from .env file

SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONNECTION_STR")
TOPIC_NAME = os.getenv("TOPIC_NAME")
SUBSCRIPTION_NAME = os.getenv("SUBSCRIPTION_NAME")




def evaluate_answer(payload: dict):
    interview_id = payload.get("interview_id")
    #user_input = payload.get("user_input")
    if not interview_id:
        logger.error("Invalid payload received in evaluate_answer: %s", payload)
        return

    logger.info(f"Evaluating answer for interview_id={interview_id}")
    db = SessionLocal()

    # Save user's answer to DB
    last_qa = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id.desc()).first()
    if last_qa and not last_qa.answer_text:
        #last_qa.answer_text = user_input
        last_qa.status = "ANSWERED"
        db.commit()

    # Generate next question or finish
    result = generate_next_question(interview_id, db)
    logger.info(f"Next step for Interview {interview_id}: {result}")

def extract_pdf_text(payload):
    logger.info(f"PDF extraction handler called with payload: {payload}")

def extract_audio_text(payload):
    logger.info(f"Audio extraction handler called with payload: {payload}")

TASK_DISPATCHER = {
    "pdf_extraction": extract_pdf_text,
    "audio_extraction": extract_audio_text,
    "evaluate_answer": evaluate_answer,
}

def handle_message(message_body):
    try:
        logger.debug(f"Received message body: {message_body}")
        data = json.loads(message_body)
        action_type = data.get("action_type")
        logger.info(f"Handling action_type: {action_type}")
        handler = TASK_DISPATCHER.get(action_type)
        if handler:
            handler(data)
        else:
            logger.warning(f"No handler for action_type: {action_type}")
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)

async def listen_to_service_bus():
    logger.info("Starting Service Bus listener.")
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=SERVICE_BUS_CONNECTION_STR)
    with servicebus_client:
        receiver = servicebus_client.get_subscription_receiver(
            topic_name=TOPIC_NAME,
            subscription_name=SUBSCRIPTION_NAME,
            receive_mode=ServiceBusReceiveMode.RECEIVE_AND_DELETE
        )
        with receiver:
            logger.info("Listening for messages on Service Bus...")
            while True:
                messages = receiver.receive_messages(max_message_count=10, max_wait_time=5)
                logger.debug(f"Received {len(messages)} messages from Service Bus.")
                for msg in messages:
                    logger.info("Processing new message from Service Bus.")
                    handle_message(str(msg))
