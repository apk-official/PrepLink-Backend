from sqlalchemy import Column, String, Integer

from app.db.base import Base


class InterviewTips(Base):
    __tablename__ = "interview_tips"
    tip_id=Column(Integer,primary_key=True,index=True)
    project_id=Column(Integer)
    tip=Column(String)