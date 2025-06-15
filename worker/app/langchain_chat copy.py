from shared.logger import logger
from shared.models import Interview, QuestionAnswer
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from sqlalchemy.orm import Session
from shared import models
   
llm = ChatOpenAI(model="gpt-4", temperature=0.7)


def generate_next_question(interview_id: int, db: Session):
    interview = db.query(models.Interview).filter_by(id=interview_id).first()
    if not interview:
        raise ValueError("Interview not found")
    user = db.query(models.User).filter_by(id=interview.user_id).first()
    if not user:
        raise ValueError("User not found")

    job_description = None
    candidate_resume = None

    if user.jd_status == "COMPLETED":
        job_description = user.jd_text
    if user.resume_status == "COMPLETED":
        candidate_resume = user.resume_text

    # Now use job_description and candidate_resume as needed
    # Load conversation history
    qas = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id).all()

    messages = [
        SystemMessage(
                content=f"""You are a professional AI interviewer. Ask only one interview question at a time based on the job description and candidate resume. Do not list multiple questions. Wait for the candidate's answer before asking the next question. End with a decision.

                Job Description:
                {job_description.strip()}

                Candidate Resume:
                {candidate_resume.strip()}
                """
            )
    ]
    for qa in qas:
        if qa.question_text:
            messages.append(AIMessage(content=qa.question_text))
        if qa.answer_text is not None and qa.answer_text.strip():
            messages.append(HumanMessage(content=qa.answer_text))
        else:
            messages.append(HumanMessage(content="SKIP"))
    question_count = len([qa for qa in qas if qa.question_text])

    if question_count >= 5:
        return "Interview Over"

    # Generate next question
    response = llm.invoke(messages)
    logger.info(f"<<< messages {messages}  >>>")
    next_question = response.content.strip()

    # Save to DB
    interview = db.query(Interview).filter_by(id=interview_id).first()
    if interview:
        new_question = QuestionAnswer(
            user_id=interview.user_id,
            interview_id=interview.id,
            question_text=next_question,
            status="NEW",
            question_id=question_count + 1
        )
        db.add(new_question)
        db.commit()
    return next_question
