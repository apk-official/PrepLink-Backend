from sqlalchemy import Column,Integer,String,Boolean,text
from sqlalchemy.orm import Mapped,mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "user"
    user_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    name=Column(String)
    email:Mapped[str]=mapped_column(String,unique=True,index=True)
    user_type=Column(String)
    img_url=Column(String)
    disabled = Column(Boolean,server_default=text('false'))
    credits=Column(Integer,server_default=text('0'))
