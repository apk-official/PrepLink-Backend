from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped,mapped_column

from app.db.base import Base


class Company(Base):
    __tablename__ = "company"
    company_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    name:Mapped[str]=mapped_column(String)
    url:Mapped[str]=mapped_column(String)
    image:Mapped[str]=mapped_column(String)

