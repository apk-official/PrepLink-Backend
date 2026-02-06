from sqlalchemy import  Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    __tablename__ = "project"
    project_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    user_id:Mapped[int]=mapped_column(Integer)
    company_id:Mapped[int]=mapped_column(Integer)
    position:Mapped[str]=mapped_column(String)
    company_name:Mapped[str]=mapped_column(String)
    company_logo:Mapped[str]=mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)