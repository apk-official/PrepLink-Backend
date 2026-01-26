from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped,mapped_column

from app.db.base import Base


class Company(Base):
    __tablename__ = "company"
    company_id=Column(Integer,primary_key=True,index=True)
    name=Column(String)
    url:Mapped[str]=mapped_column(String)

