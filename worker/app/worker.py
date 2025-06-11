# worker/app/worker.py
import json
from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode

#from db import Session, Interview
from shared.models import Interview, QuestionAnswer, User  # Add this import
from shared.database import SessionLocal
from worker.app.langchain_chat import generate_next_question
from worker.app.pdf_to_text import extract_text_from_pdf  # Add this import
from worker.app.audio_to_text import extract_text_from_audio  # Add this import
from dotenv import load_dotenv
#from worker.app.langgraph_interview import graph
import os
#from shared.models import Interview, QuestionAnswer
from shared.logger import logger




load_dotenv()  # Load environment variables from .env file

SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONNECTION_STR")
TOPIC_NAME = os.getenv("TOPIC_NAME")
SUBSCRIPTION_NAME = os.getenv("SUBSCRIPTION_NAME")




def next_question(payload: dict):
    inner_payload = payload.get("payload", {})
    interview_id = inner_payload.get("interview_id")
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

def extract_audio_text(payload: dict):
    """
    Handles audio_extraction task: extracts text from audio and updates the DB.
    Uses the audio_recording_path from the QuestionAnswer record.
    """
    inner_payload = payload.get("payload", {})
    interview_id = inner_payload.get("interview_id")
    question_id = inner_payload.get("question_id")
    user_id = payload.get("user_id")

    if not interview_id or not question_id or not user_id:
        logger.error("Invalid payload received in extract_audio_text: %s", payload)
        return

    db = SessionLocal()
    try:
        qa = db.query(QuestionAnswer).filter_by(interview_id=interview_id, question_id=question_id).first()
        if not qa:
            logger.error(f"QuestionAnswer not found for interview_id={interview_id}, question_id={question_id}")
            db.close()
            return

        # Always resolve path from project root
        audio_path = qa.audio_recording_path
        abs_audio_path = os.path.abspath(audio_path)
        if not os.path.exists(abs_audio_path):
            logger.error(f"Audio file not found at path: {abs_audio_path}")
            db.close()
            return

        logger.info(f"Starting audio extraction for user_id={user_id}, interview_id={interview_id}, question_id={question_id}, audio_path={abs_audio_path}")

        # Extract text from audio
        answer_text = extract_text_from_audio(abs_audio_path)
        qa.answer_text = answer_text
        if hasattr(qa, "IS_Candidate_Answer_Processed"):
            qa.IS_Candidate_Answer_Processed = True  # Only if column exists

        db.commit()
        logger.info(f"Audio processed and answer_text updated for QuestionAnswer id={qa.id}")
    except Exception as e:
        logger.error(f"Error processing audio for interview_id={interview_id}, question_id={question_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def doc_upload(payload: dict):
    inner_payload = payload.get("payload", {})
    user_id = payload.get("user_id")
    file_type = inner_payload.get("file_type")
    file_path = inner_payload.get("file_path")

    if not user_id or not file_type or not file_path:
        logger.error("Invalid payload received in doc_upload: %s", payload)
        return

    logger.info(f"Starting doc_upload for user_id={user_id}, file_type={file_type}, file_path={file_path}")
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.error(f"User with id {user_id} not found.")
        db.close()
        return

    # Set status to PROCESSING
    if file_type.lower() == "jd":
        user.jd_status = "PROCESSING"
    elif file_type.lower() == "resume":
        user.resume_status = "PROCESSING"
    else:
        logger.error(f"Invalid file_type: {file_type}")
        db.close()
        return
    db.commit()

    try:
        extracted_text = extract_text_from_pdf(file_path)
        if file_type.lower() == "jd":
            user.jd_text = extracted_text
            user.jd_status = "COMPLETED"
        elif file_type.lower() == "resume":
            user.resume_text = extracted_text
            user.resume_status = "COMPLETED"
        db.commit()
        logger.info(f"Document {file_type} for user_id={user_id} processed and updated successfully.")
    except Exception as e:
        logger.error(f"Error extracting text from {file_type} for user_id={user_id}: {e}", exc_info=True)
        if file_type.lower() == "jd":
            user.jd_status = "FAILED"
        elif file_type.lower() == "resume":
            user.resume_status = "FAILED"
        db.commit()
    finally:
        db.close()

TASK_DISPATCHER = {
    "pdf_extraction": extract_pdf_text,
    "audio_extraction": extract_audio_text,
    "next_question": next_question,
    "doc_upload": doc_upload,
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
