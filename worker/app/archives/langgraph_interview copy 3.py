from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from langchain_core.runnables import Runnable
from sqlalchemy.orm import Session

#from app.models import QuestionAnswer
from shared.models import Interview, QuestionAnswer
from shared.database import SessionLocal
from shared.logger import logger

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# Define LangGraph state schema
class InterviewState(dict):
    interview_id: int
    question_count: int
    decision: str | None
    history: list  # List of AIMessage and HumanMessage

# Load state from DB
def get_state_from_db(interview_id: int, db: Session) -> InterviewState:
    logger.info(f"Loading state from DB for interview_id={interview_id}")
    qas = db.query(QuestionAnswer).filter_by(interview_id=interview_id).order_by(QuestionAnswer.id).all()
    history = []
    for qa in qas:
        if qa.question_text:
            history.append(AIMessage(content=qa.question_text))
        if qa.answer_text:
            history.append(HumanMessage(content=qa.answer_text))
    logger.debug(f"Loaded {len(qas)} QAs from DB for interview_id={interview_id}")
    return InterviewState({
        "interview_id": interview_id,
        "question_count": len([qa for qa in qas if qa.answer_text]),
        "decision": None,
        "history": history
    })

# Save state to DB
def store_state_to_db(state: InterviewState, db: Session):
    interview_id = state["interview_id"]
    history = state["history"]
    logger.info(f"Storing state to DB for interview_id={interview_id}")

    # Extract latest Q&A
    question, answer = None, None
    for msg in reversed(history):
        if isinstance(msg, HumanMessage) and answer is None:
            answer = msg.content
        elif isinstance(msg, AIMessage) and question is None:
            question = msg.content
        if question and answer:
            break

    if question:
        qa = QuestionAnswer(
            interview_id=interview_id,
            question_text=question,
            answer_text=answer,
            status="ANSWERED" if answer else "NEW"
        )
        db.add(qa)
        db.commit()
        logger.debug(f"Saved Q&A to DB for interview_id={interview_id}: Q='{question}' | A='{answer}'")
    else:
        logger.warning(f"No new Q&A found to store for interview_id={interview_id}")

# Interview logic node
def interview_node(state: dict) -> dict:
    session: Session = SessionLocal()
    interview_id = state["interview_id"]
    question_count = state["question_count"]
    messages = state.get("history", [])

    logger.info(f"Running interview_node for interview_id={interview_id} | question_count={question_count}")

    # First question setup
    job_description = """
    We are looking for a Cloud Solutions Architect with expertise in Azure, GenAI integration, and Python-based automation. The ideal candidate will lead cloud-native transformation and AI-powered modernization initiatives.
    """

    candidate_resume = """
    Vijay Saini
    Experience: 10+ years
    Skills: Azure, GenAI, Python, Terraform, Kubernetes
    Certifications: CKAD, Azure AI Fundamentals, Azure DevOps Expert
    Projects: Led GenAI RAG pipeline on Azure OpenAI, built microservices platform on AKS
    """

    if question_count == 0:
        logger.debug("First question: initializing interview with intro and first prompt.")
        messages = [
            SystemMessage(
                content=f"""You are a professional AI interviewer. Ask questions based on the job description and candidate resume. End with a decision.

                Job Description:
                {job_description.strip()}

                Candidate Resume:
                {candidate_resume.strip()}
                """
            )
        ]
    else:
        logger.debug("Generating next interview question.")
        messages.append(SystemMessage(content="Ask the next interview question."))

    # Call LLM
    response = llm.invoke(messages)
    print("messages", messages)
    next_question = response.content.strip()
    logger.debug(f"LLM response: {next_question}")
    messages.append(response)

    # Save to DB
    try:
        interview = session.query(Interview).filter_by(id=interview_id).first()
        if interview:
            new_question = QuestionAnswer(
                user_id=interview.user_id,
                interview_id=interview.id,
                question_text=next_question,
                status="NEW",
                question_id=question_count + 1
            )
            session.add(new_question)
            session.commit()
            logger.info(f"Question saved to DB for interview_id={interview_id}")
        else:
            logger.warning(f"No interview found for interview_id={interview_id}")
    except Exception as e:
        logger.error(f"Error saving question to DB: {e}")
    finally:
        session.close()

    return {
        **state,
        "history": messages,
        "question_count": question_count + 1
    }


# Decision logic node
def make_decision(state: InterviewState) -> InterviewState:
    logger.info(f"Running make_decision for interview_id={state['interview_id']} | question_count={state['question_count']}")
    if state["question_count"] < 3:
        logger.debug("Not enough questions answered to make a decision.")
        return state  # Force minimum 3 questions

    if state["decision"] is None:
        logger.debug("Making final hire/no hire decision.")
        messages = state["history"] + [SystemMessage(content="Based on the above, make a final Hire or No Hire decision.")]
        response = llm.invoke(messages)
        logger.debug(f"LLM decision response: {response.content}")
        state["history"].append(response)
        state["decision"] = "Hire" if "hire" in response.content.lower() else "No Hire"
        logger.info(f"Decision made: {state['decision']}")
    return state

# Should we decide now?
def check_if_done(state: InterviewState):
    done = state["question_count"] >= 5 or state["decision"] is not None
    logger.debug(f"Checking if interview is done for interview_id={state['interview_id']}: {done}")
    return done

# Build the graph
graph_builder = StateGraph(InterviewState)
graph_builder.add_node("interview", interview_node)
graph_builder.add_node("make_decision", make_decision)
graph_builder.set_entry_point("interview")

# Decision condition
graph_builder.add_conditional_edges(
    "interview",
    check_if_done,
    {
        True: "make_decision",   # `recursion_check` = True
        False: "interview"       # `recursion_check` = False
    }
)


# End the graph after decision
graph_builder.set_finish_point("make_decision")



graph = graph_builder.compile()