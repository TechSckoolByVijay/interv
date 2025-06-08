from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    user_type = Column(String)
    interviews = relationship("Interview", back_populates="user")
    jd_path = Column(String, nullable=True)
    resume_path = Column(String, nullable=True)

class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interview_name = Column(String)
    user = relationship("User", back_populates="interviews")

class QuestionAnswer(Base):
    __tablename__ = "question_answers"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    question_id = Column(Integer)
    question_text = Column(Text)
    status = Column(String, default="NEW")
    answer_text = Column(Text, nullable=True)
    camera_recording_path = Column(String, nullable=True)
    screen_recording_path = Column(String, nullable=True)
    audio_recording_path = Column(String, nullable=True)
    combined_recording_path = Column(String, nullable=True)
    ai_answer = Column(Text, nullable=True)
    ai_remark = Column(Text, nullable=True)
    candidate_score = Column(Float, nullable=True)
    candidate_grade = Column(String, nullable=True)