# worker/app/worker.py
import json
from azure.servicebus import ServiceBusClient, ServiceBusReceiveMode

#from db import Session, Interview
from shared.models import Interview, QuestionAnswer, User  # Add this import
from shared.database import SessionLocal
from worker.app.langchain_chat import generate_next_question, llm  # Ensure llm is imported or initialized
from worker.app.pdf_to_text import extract_text_from_pdf  # Add this import
from worker.app.audio_to_text import extract_text_from_audio  # Add this import
from dotenv import load_dotenv
#from worker.app.langgraph_interview import graph
import os
#from shared.models import Interview, QuestionAnswer
from shared.logger import logger
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import ChatOpenAI


load_dotenv()  # Load environment variables from .env file

SERVICE_BUS_CONNECTION_STR = os.getenv("SERVICE_BUS_CONNECTION_STR")
TOPIC_NAME = os.getenv("TOPIC_NAME")
SUBSCRIPTION_NAME = os.getenv("SUBSCRIPTION_NAME")




GRADE_SCALE = [
    (9, "A"),
    (8, "B"),
    (7, "C"),
    (5, "D"),
    (3, "E"),
    (0, "F"),
]

def grade_score(score):
    for min_score, grade in GRADE_SCALE:
        if score >= min_score:
            return grade
    return "F"

llm = ChatOpenAI(model="gpt-4", temperature=0.7)


def performance_measure(payload: dict):
    """
    Evaluates all answers in an interview, generates ideal answers, scores, and grades.
    Also updates overall interview score and pass/fail status.
    """
    inner_payload = payload.get("payload", {})
    interview_id = inner_payload.get("interview_id")
    if not interview_id:
        logger.error("No interview_id in payload: %s", payload)
        return

    db = SessionLocal()
    try:
        interview = db.query(Interview).filter_by(id=interview_id).first()
        if not interview:
            logger.error(f"Interview {interview_id} not found")
            return
        user = db.query(User).filter_by(id=interview.user_id).first()
        if not user:
            logger.error(f"User {interview.user_id} not found")
            return

        jd = user.jd_text or ""
        resume = user.resume_text or ""

        qas = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id).all()
        total_score = 0
        total_questions = 0
        pass_count = 0

        for qa in qas:
            if not qa.question_text or not qa.answer_text:
                continue

            # Generate ideal answer using LLM
            prompt = (
                f"Job Description:\n{jd}\n\n"
                f"Candidate Resume:\n{resume}\n\n"
                f"Question: {qa.question_text}\n"
                "What is the ideal answer to this question for this job? Respond concisely."
            )
            ai_answer = llm.invoke([HumanMessage(content=prompt)]).content.strip()

            # Compare user's answer to ideal answer
            compare_prompt = (
                f"Job Description:\n{jd}\n\n"
                f"Candidate Resume:\n{resume}\n\n"
                f"Question: {qa.question_text}\n"
                f"Ideal Answer: {ai_answer}\n"
                f"Candidate's Answer: {qa.answer_text}\n"
                "Score the candidate's answer out of 10 and assign a grade (A=best, F=fail). "
                "Respond in JSON: {\"score\": <int>, \"grade\": \"A-F\"} and a short justification."
            )
            compare_response = llm.invoke([HumanMessage(content=compare_prompt)]).content.strip()

            # Parse response (simple extraction)
            import re, json
            try:
                json_match = re.search(r'\{.*?\}', compare_response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                    score = int(result.get("score", 0))
                    grade = result.get("grade", "F")
                else:
                    score = 0
                    grade = "F"
            except Exception:
                score = 0
                grade = "F"

            # Update DB
            qa.ai_answer = ai_answer
            qa.candidate_score = score
            qa.candidate_grade = grade
            db.commit()
            logger.info(f"Evaluated Q{qa.id}: score={score}, grade={grade}")

            total_score += score
            total_questions += 1
            if grade != "F":
                pass_count += 1

        # Calculate overall score in percentage
        if total_questions > 0:
            max_total = total_questions * 10
            score_percentage = (total_score / max_total) * 100
            interview.score_in_percentage = f"{score_percentage:.2f}"
            # Pass if at least 60% of questions are not 'F'
            interview_cleared = "Pass" if pass_count / total_questions >= 0.6 else "Fail"
            interview.interview_cleared_by_candidate = interview_cleared
        else:
            interview.score_in_percentage = "0.00"
            interview.interview_cleared_by_candidate = "Fail"

        # After evaluating all questions, update interview status
        interview.status = "AI_EVALUATION_DONE"
        db.commit()
        logger.info(f"Interview {interview_id} status updated to AI_EVALUATION_DONE, score: {interview.score_in_percentage}, result: {interview.interview_cleared_by_candidate}")

    except Exception as e:
        logger.error(f"Error in performance_measure: {e}", exc_info=True)
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
 

def process_question(payload: dict):
    """
    Handles audio_extraction: extracts text from audio, updates the DB,
    marks answer as processed, and generates the next question.
    """
    inner_payload = payload.get("payload", {})
    interview_id = inner_payload.get("interview_id")
    question_id = inner_payload.get("question_id")
    user_id = payload.get("user_id")

    if not interview_id or not question_id or not user_id:
        logger.error("Invalid payload received in process_question: %s", payload)
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

        # Save user's answer to DB
        last_qa = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id.desc()).first()
        if last_qa and not last_qa.answer_text:
            #last_qa.answer_text = user_input
            last_qa.status = "ANSWERED"
            db.commit()

        # Extract text from audio
        answer_text = extract_text_from_audio(abs_audio_path)
        qa.answer_text = answer_text
        qa.status = "Answer_Audio_Extracted"
        db.commit()
        logger.info(f"Audio processed and answer_text updated for QuestionAnswer id={qa.id}")

        # Generate next question or finish
        result = generate_next_question(interview_id, db)
        logger.info(f"Next step for Interview {interview_id}: {result}")
        

    except Exception as e:
        logger.error(f"Error processing audio for interview_id={interview_id}, question_id={question_id}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

# Update the dispatcher to use process_question for audio_extraction
TASK_DISPATCHER = {
    "process_question": process_question,
    "doc_upload": doc_upload,
    "performance_measure": performance_measure,
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
