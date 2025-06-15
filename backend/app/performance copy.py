from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from shared import models
from shared.database import SessionLocal
from shared import schemas
from typing import List
from shared.logger import logger


router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/interviews/{user_id}", response_model=List[schemas.InterviewSummary])
def list_completed_interviews(user_id: int, db: Session = Depends(get_db)):
    interviews = db.query(models.Interview).filter_by(user_id=user_id).all()
    summaries = []
    for interview in interviews:
        candidate_name = interview.user.username if interview.user else ""
        qa = (
            db.query(models.QuestionAnswer)
            .filter_by(interview_id=interview.id)
            .order_by(models.QuestionAnswer.id.desc())
            .first()
        )
        candidate_grade = qa.candidate_grade if qa else None

        summaries.append(
            schemas.InterviewSummary(
                id=interview.id,
                user_id=interview.user_id,
                interview_name=interview.interview_name,
                status=interview.status,
                score_in_percentage=interview.score_in_percentage,
                interview_cleared_by_candidate=interview.interview_cleared_by_candidate,
                candidate_name=candidate_name,
                candidate_grade=candidate_grade,
            )
        )
    logger.info(f"summaries {summaries}")
    return summaries

@router.get("/interview/{interview_id}/details", response_model=schemas.InterviewDetails)
def interview_details(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter_by(id=interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    questions = db.query(models.QuestionAnswer).filter_by(interview_id=interview_id).all()
    return schemas.InterviewDetails(
        interview=schemas.Interview.from_orm(interview),
        questions=[schemas.QuestionAnswer.from_orm(q) for q in questions]
    )