from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Interview(Base):
    __tablename__ = "interviews"
    session_id = Column(String, primary_key=True)
    history = Column(JSON)
    question_count = Column(Integer)
    decision = Column(String)

engine = create_engine("sqlite:///interviews.db")
Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
