from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared import models
from shared.database import SessionLocal
from shared import schemas
from typing import List

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
    return interviews

@router.get("/interview/{interview_id}/details", response_model=schemas.InterviewDetails)
def interview_details(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.Interview).filter_by(id=interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    questions = db.query(models.QuestionAnswer).filter_by(interview_id=interview_id).all()
    return schemas.InterviewDetails(
        interview=interview,
        questions=questions
    )