from shared.logger import logger
from shared.models import Interview, QuestionAnswer
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from sqlalchemy.orm import Session
from shared import models
from backend.app.util_queue import (
    send_message_to_service_bus,
    QuestionProcessPayload,
    ServiceBusMessageModel
)
from datetime import datetime
from uuid import uuid4
   
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

MAX_QUESTIONS = 5
    
    
def generate_next_question(interview_id: int, db: Session):
    logger.info(f"Generating next question for interview_id={interview_id}")
    interview = db.query(models.Interview).filter_by(id=interview_id).first()
    if not interview:
        logger.error(f"Interview not found for interview_id={interview_id}")
        raise ValueError("Interview not found")
    user = db.query(models.User).filter_by(id=interview.user_id).first()
    if not user:
        logger.error(f"User not found for user_id={interview.user_id}")
        raise ValueError("User not found")

    job_description = user.jd_text if user.jd_status == "COMPLETED" else None
    candidate_resume = user.resume_text if user.resume_status == "COMPLETED" else None

    qas = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id).all()
    logger.debug(f"Found {len(qas)} previous question-answer pairs for interview_id={interview_id}")

    messages = [
        SystemMessage(
            content=f"""You are a professional AI interviewer. 
            Ask only one interview question at a time based on the job description and candidate resume. 
            
            Do not list multiple questions. Wait for the candidate's answer before asking the next question. When you reach the last question (Question {len(qas)+1} out of {MAX_QUESTIONS}), instead of asking a question, generate a professional closing note to end the interview.

            Job Description:
            {job_description.strip() if job_description else ''}

            Candidate Resume:
            {candidate_resume.strip() if candidate_resume else ''}
            """
        )
    ]

    # Append previous questions with their count
    question_number = 1
    for qa in qas:
        if qa.question_text:
            messages.append(AIMessage(content=f"{qa.question_text}"))
            question_number += 1
        if qa.answer_text is not None and qa.answer_text.strip():
            messages.append(HumanMessage(content=qa.answer_text))
        else:
            messages.append(HumanMessage(content="SKIP"))
    question_count = question_number - 1

    logger.info(f"Current question count: {question_count} for interview_id={interview_id}")

    if question_count >= MAX_QUESTIONS:
        interview.status = "DONE_ASKING_QUESTIONS"
        db.commit()
        logger.info(f"Interview {interview_id} already completed.")
        return "Interview already completed."

    # If it's the last question, instruct AI to generate a closing note
    if question_count == MAX_QUESTIONS - 1:
        messages.append(SystemMessage(
            content=f"This is the last question. Instead of asking a question, generate a professional closing note to end the interview."
        ))

    logger.debug(f"Invoking LLM for interview_id={interview_id} with {len(messages)} messages")
    response = llm.invoke(messages)
    next_content = response.content.strip()
    logger.info(f"LLM response for interview_id={interview_id}: {next_content}")

    # Save to DB including the closing note as a regular question
    new_question = QuestionAnswer(
        user_id=interview.user_id,
        interview_id=interview.id,
        question_text=next_content,
        status="NEW",
        question_id=question_count + 1
    )
    db.add(new_question)
    db.commit()
    logger.info(f"Saved new question {question_count + 1} for interview_id={interview_id}")

    # If closing note, update interview status and send message to service bus
    if question_count == MAX_QUESTIONS - 1:
        interview.status = "DONE_ASKING_QUESTIONS"
        db.commit()
        logger.info(f"Interview {interview_id} marked as DONE_ASKING_QUESTIONS")

    return next_content
