from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from shared import models
from shared import schemas
from shared.database import SessionLocal
from typing import List
from shared.logger import logger
import os
from .util_queue import send_message_to_service_bus
from datetime import datetime
import uuid
from uuid import uuid4
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime
from backend.app.util_queue import (
    send_message_to_service_bus,
    FileProcessPayload,
    ServiceBusMessageModel, 
    QuestionProcessPayload
)
import time  # Add this import at the top if not present


router = APIRouter()



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dummy questions for demonstration
QUESTION_BANK = [
    {"question_id": 1, "question_text": "hello and welcome to this interview. Can we startwith a quick introduction of yours?"},
]

@router.post("/interview")
def create_interview(interview: schemas.InterviewCreate, db: Session = Depends(get_db)):
    logger.info(f"/interview called with interview_name={interview.interview_name}, user_id={interview.user_id}")  # <-- log params
    db_interview = models.Interview(
        interview_name=interview.interview_name,
        user_id=interview.user_id,
        status="NEW"
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    # Remove or fix the next logger line if payload is not defined
    # logger.info(f"Starting Interview for user {payload.user_id} interview {payload.interview_id}")
    return db_interview


@router.get("/interview/{interview_id}/status")
def get_interview_status(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter_by(id=interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return {"interview_id": interview.id, "status": interview.status}


@router.post("/queue_next_question/{user_id}/{interview_id}")
def queue_next_question(
    user_id: int,
    interview_id: int,
):
    payload = FileProcessPayload(docPath="", fileType="")
    correlationId = str(uuid4())
    message = ServiceBusMessageModel(
        correlationId=correlationId,
        session_id=f"{user_id}-{interview_id}",
        action_type="next_question",
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        status="asking for next question",
        payload=payload
    )
    logger.info(f"Queuing next_question message to service bus: {message}")
    send_message_to_service_bus(message.dict())

    return {"message": "Queued next_question", "correlationId": correlationId}


@router.post("/start_interview", response_model=List[schemas.QuestionAnswerOut])
def start_interview(payload: schemas.QuestionAnswerCreate, db: Session = Depends(get_db)):
    # Pick 3 new questions (could be random or sequential)
    selected_questions = QUESTION_BANK[:3]
    created = []
    for q in selected_questions:
        qa = models.QuestionAnswer(
            user_id=payload.user_id,
            interview_id=payload.interview_id,
            question_id=q["question_id"],
            question_text=q["question_text"],
            status="NEW"
        )
        db.add(qa)
        db.commit()
        db.refresh(qa)
        created.append(qa)
        logger.info(f"Inserted question {q['question_id']} for user {payload.user_id} interview {payload.interview_id}")
    return created


@router.post("/more_questions", response_model=List[schemas.QuestionAnswerOut])
def more_questions(payload: schemas.QuestionAnswerCreate, db: Session = Depends(get_db)):
    # Check interview status first
    interview = db.query(models.Interview).filter_by(id=payload.interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.status == "DONE_ASKING_QUESTIONS":
        logger.info(f"Interview {payload.interview_id} is COMPLETED. No more questions will be fetched.")

        # Add service bus message logic (same as end_interview)
        try:
            correlationId = str(uuid4())
            sb_payload = QuestionProcessPayload(
                interview_id=str(interview.id),
                question_id=0
            )
            message = ServiceBusMessageModel(
                correlationId=correlationId,
                session_id=f"{interview.user_id}-{interview.id}",
                action_type="performance_measure",
                user_id=interview.user_id,
                timestamp=datetime.utcnow().isoformat(),
                status="interview ended",
                payload=sb_payload
            )
            logger.info(f"Queuing end_interview message to service bus from more_questions: {message}")
            send_message_to_service_bus(message.dict())
        except Exception as e:
            logger.error(f"Failed to send end_interview message from more_questions: {e}")

        return []

    # Try up to 6 times with 3 seconds sleep if no questions found
    for attempt in range(20):
        new_questions = db.query(models.QuestionAnswer).filter_by(
            user_id=payload.user_id,
            interview_id=payload.interview_id,
            status="NEW"
        ).all()
        if new_questions:
            logger.info(f"Fetched {len(new_questions)} NEW questions for user {payload.user_id} interview {payload.interview_id} on attempt {attempt+1}")
            return new_questions
        logger.info(f"No NEW questions found for user {payload.user_id} interview {payload.interview_id} on attempt {attempt+1}. Retrying in 3 seconds...")
        time.sleep(3)
    logger.info(f"No NEW questions found after 15 attempts for user {payload.user_id} interview {payload.interview_id}")
    return []


@router.post("/upload_answer/{user_id}/{interview_id}/{question_id}/{type}")
async def upload_answer_type(
    user_id: int,
    interview_id: int,
    question_id: int,
    type: str,
    file: UploadFile = File(...)
):
    # Save file logic...
    file_path = f"uploads/{user_id}/{interview_id}/{question_id}_{type}_{file.filename}"
    
    allowed_types = {"audio", "camera", "screen", "combined"}
    if type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid recording type")
    upload_dir = f"uploads/{user_id}/{interview_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    logger.info(f"Saved {type} recording at {os.path.abspath(file_path)}")

    return {"path": file_path}



# /question API updates the status of question after user answers it.
@router.patch("/question/{qa_id}", response_model=schemas.QuestionAnswerOut)
def update_question_answer(qa_id: int, update: schemas.QuestionAnswerUpdate, db: Session = Depends(get_db)):
    qa = db.query(models.QuestionAnswer).filter_by(id=qa_id).first()
    if not qa:
        raise HTTPException(status_code=404, detail="QuestionAnswer not found")
    for field, value in update.dict(exclude_unset=True).items():
        setattr(qa, field, value)
    db.commit()
    db.refresh(qa)
    logger.info(f"Updated QuestionAnswer {qa_id} with {update.dict(exclude_unset=True)}")

    # Enqueue next_question message to service bus
    correlationId = str(uuid4())
    payload = QuestionProcessPayload(
        interview_id=str(qa.interview_id),
        question_id=str(qa.question_id)
    )
    message = ServiceBusMessageModel(
        correlationId=correlationId,
        session_id=f"{qa.user_id}-{qa.interview_id}",
        action_type="process_question",
        user_id=qa.user_id,
        timestamp=datetime.utcnow().isoformat(),
        status="asking for next question",
        payload=payload
    )
    logger.info(f"Queuing next_question message to service bus: {message}")
    send_message_to_service_bus(message.dict())

    return qa


@router.post("/end_interview/{interview_id}")
async def end_interview(interview_id: int, db: Session = Depends(get_db)):
    """
    Ends the interview and sends a performance measure message to the service bus.
    """
    try:
        # Fetch interview details using interview_id
        interview = db.query(models.Interview).filter_by(id=interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        user_id = interview.user_id

        correlationId = str(uuid4())
        payload = QuestionProcessPayload(
            interview_id=str(interview_id),
            question_id=0
        )
        message = ServiceBusMessageModel(
            correlationId=correlationId,
            session_id=f"{user_id}-{interview_id}",
            action_type="performance_measure",
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            status="interview ended",
            payload=payload
        )
        logger.info(f"Queuing end_interview message to service bus: {message}")
        send_message_to_service_bus(message.dict())
        return {"message": "Interview ended and message sent to service bus."}
    except Exception as e:
        logger.error(f"Failed to end interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to end interview")

