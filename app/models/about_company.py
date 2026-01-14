from sqlalchemy import Column, Integer,String

from app.db.base import Base


class AboutCompany(Base):
    __tablename__ = "about_company"
    about_company_id=Column(Integer,primary_key=True,index=True)
    project_id=Column(Integer)
    vision=Column(String)
    mission=Column(String)
    additional=Column(String)
