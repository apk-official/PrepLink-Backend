from sqlalchemy import Column, Integer, String

from app.db.base import Base


class Project(Base):
    __tablename__ = "Project"
    project_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer)
    company_id=Column(Integer)
    position=Column(String)
    created_at=Column(String)