from sqlalchemy import Column, Integer,String

from app.db.base import Base


class InterviewQuestions(Base):
    __tablename__ = "interview_question"
    question_id=Column(Integer,primary_key=True,index=True)
    project_id=Column(Integer)
    question_type=Column(String)
    answer=Column(String)
