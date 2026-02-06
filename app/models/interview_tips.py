from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InterviewTips(Base):
    __tablename__ = "interview_tips"
    tip_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    project_id:Mapped[int]=mapped_column(Integer)
    tip:Mapped[str]=mapped_column(String)
    tip_url:Mapped[str]=mapped_column(String)