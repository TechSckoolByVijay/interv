from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    user_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class InterviewCreate(BaseModel):
    interview_name: str

class QuestionAnswerCreate(BaseModel):
    user_id: int
    interview_id: int

class QuestionAnswerUpdate(BaseModel):
    answer_text: Optional[str] = None
    camera_recording_path: Optional[str] = None
    screen_recording_path: Optional[str] = None
    audio_recording_path: Optional[str] = None
    combined_recording_path: Optional[str] = None
    status: Optional[str] = None
    ai_answer: Optional[str] = None
    ai_remark: Optional[str] = None
    candidate_score: Optional[float] = None
    candidate_grade: Optional[str] = None

class QuestionAnswerOut(BaseModel):
    id: int
    user_id: int
    interview_id: int
    question_id: int
    question_text: str
    status: str
    answer_text: Optional[str]
    camera_recording_path: Optional[str]
    screen_recording_path: Optional[str]
    audio_recording_path: Optional[str]
    combined_recording_path: Optional[str]
    ai_answer: Optional[str]
    ai_remark: Optional[str]
    candidate_score: Optional[float]
    candidate_grade: Optional[str]

    class Config:
        orm_mode = True

class InterviewSummary(BaseModel):
    id: int
    interview_name: str
    timestamp: str
    candidate_grade: str

    class Config:
        orm_mode = True

class InterviewDetails(BaseModel):
    interview: InterviewSummary
    questions: List[QuestionAnswerOut]