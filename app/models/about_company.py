from sqlalchemy import Column, Integer,String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class AboutCompany(Base):
    __tablename__ = "about_company"
    about_company_id=Column(Integer,primary_key=True,index=True)
    project_id:Mapped[int]=mapped_column(Integer)
    vision:Mapped[str]=mapped_column(String)
    vision_url:Mapped[str]=mapped_column(String)
    mission:Mapped[str]=mapped_column(String)
    mission_url:Mapped[str]=mapped_column(String)
    additional:Mapped[str]=mapped_column(String)
    additional_url:Mapped[str]=mapped_column(String)
