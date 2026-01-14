from sqlalchemy import Column,Integer,String,Boolean

from app.db.base import Base


class User(Base):
    __tablename__ = "user"
    user_id=Column(Integer,primary_key=True,index=True)
    name=Column(String)
    email=Column(String)
    user_type=Column(String)
    img_url=Column(String)
    disabled = Column(Boolean)
    credits=Column(Integer)
