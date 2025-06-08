# AI Interviewer Backend – Developer Knowledge Transfer (KT)

Welcome to the AI Interviewer backend! This document will help you understand the codebase, its structure, and how the main components interact. We use [FastAPI](https://fastapi.tiangolo.com/) for the web framework and [SQLAlchemy](https://docs.sqlalchemy.org/) for ORM/database access.

---

## 1. Entry Point: `main.py`

This is the application’s entry point. It creates the FastAPI app, sets up CORS, includes routers, and initializes the database.

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .interview import router as interview_router
from .jd_resume import router as jd_resume_router
from .performance import router as performance_router
from .database import Base, engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth")
app.include_router(interview_router, prefix="/interview")
app.include_router(jd_resume_router, prefix="/jd_resume")
app.include_router(performance_router, prefix="/api/performance")

Base.metadata.create_all(bind=engine)
```

**Key Points:**
- **Routers** modularize endpoints.
- **CORS** allows cross-origin requests (important for frontend-backend separation).
- **Database tables** are created at startup.

**References:**  
- [FastAPI Routers](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)

---

## 2. Database Models: `models.py`

Defines the SQLAlchemy ORM models for users, interviews, and question answers.

```python
# models.py
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
```
- **User**: Stores user credentials, type, and document paths.

```python
class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    interview_name = Column(String)
    user = relationship("User", back_populates="interviews")
```
- **Interview**: Linked to a user, stores interview sessions.

```python
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
```
- **QuestionAnswer**: Stores answers, recordings, AI feedback, and scores.

**References:**  
- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

---

## 3. Pydantic Schemas: `schemas.py`

Defines request/response models for data validation and serialization.

```python
from pydantic import BaseModel
from typing import Optional, List

class UserCreate(BaseModel):
    username: str
    password: str
    user_type: str

class UserLogin(BaseModel):
    username: str
    password: str
```
- Used for user registration and login.

```python
class InterviewCreate(BaseModel):
    interview_name: str

class QuestionAnswerCreate(BaseModel):
    user_id: int
    interview_id: int
```
- Used for creating interviews and question-answer records.

```python
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
```
- Used for updating answers and related metadata.

```python
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
```
- Used for serializing question-answer data from the database.

**References:**  
- [Pydantic Models](https://docs.pydantic.dev/latest/usage/models/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)

---

## 4. Database Connection: `database.py`

Sets up the SQLAlchemy engine and session.

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```
- **engine**: Connects to the database.
- **SessionLocal**: Used for DB sessions in endpoints.
- **Base**: Base class for ORM models.

**References:**  
- [SQLAlchemy Engine](https://docs.sqlalchemy.org/en/20/core/engines.html)

---

## 5. Configuration: `config.py`

Loads environment variables and settings.

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
```
- Reads settings from `.env` file.

**References:**  
- [Pydantic Settings Management](https://docs.pydantic.dev/latest/usage/pydantic_settings/)

---

## 6. Logging: `logger.py`

Configures logging for the application.

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```
- Use `logger.info()`, `logger.error()`, etc., for logging.

---

## 7. Routers: API Endpoints

Each router handles a specific set of endpoints.

### a. `auth.py` – Authentication

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .schemas import UserCreate, UserLogin
from .models import User
from .database import get_db

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Registration logic
```
- Handles `/signup` and `/login` endpoints.

### b. `interview.py` – Interview Management

```python
@router.post("/start_interview")
def start_interview(...):
    # Interview creation logic

@router.post("/answer_question")
def answer_question(...):
    # Answer submission logic
```
- Handles interview sessions and question answers.

### c. `jd_resume.py` – JD/Resume Upload

```python
@router.post("/upload_jd")
def upload_jd(...):
    # JD upload logic

@router.post("/upload_resume")
def upload_resume(...):
    # Resume upload logic
```
- Handles file uploads and management.

### d. `performance.py` – Performance Tracking

```python
@router.get("/summary")
def get_summary(...):
    # Returns interview summaries

@router.get("/details/{interview_id}")
def get_details(interview_id: int, ...):
    # Returns detailed interview results
```
- Provides endpoints for performance analytics.

**References:**  
- [FastAPI Path Operations](https://fastapi.tiangolo.com/tutorial/path-operation-decorators/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)

---

## 8. Typical Request Flow

1. **User registers/logs in** (`/auth/signup`, `/auth/login`).
2. **User starts an interview** (`/interview/start_interview`).
3. **User answers questions, uploads files** (`/interview/answer_question`, `/jd_resume/upload_*`).
4. **User checks performance** (`/api/performance/summary`, `/api/performance/details/{id}`).

---

## 9. Useful References

- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM Docs](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic Docs](https://docs.pydantic.dev/latest/)
- [Python Logging](https://docs.python.org/3/library/logging.html)

---

## 10. Tips for New Developers

- Follow the modular structure: keep endpoints, models, and schemas in their respective files.
- Use Pydantic models for all request/response validation.
- Use SQLAlchemy sessions (`db: Session = Depends(get_db)`) for all DB operations.
- Log important actions and errors for easier debugging.
- Check the `.env` file for environment-specific settings.

---

Welcome aboard! If you have questions, check the references above or ask your team.