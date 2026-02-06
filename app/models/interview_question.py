from sqlalchemy import Column, Integer,String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InterviewQuestions(Base):
    __tablename__ = "interview_question"
    question_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    project_id:Mapped[int]=mapped_column(Integer)
    question_type:Mapped[str]=mapped_column(String)
    question:Mapped[str]=mapped_column(String)
    answer:Mapped[str]=mapped_column(String)
