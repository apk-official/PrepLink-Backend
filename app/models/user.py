from sqlalchemy import Column, Integer, String
from app.db.base import Base


class Users(Base):
    """
        SQLAlchemy model for the 'users' table.
        This table stores user credentials such as username and hashed password.
    """
    __tablename__='users'

    id = Column(Integer,primary_key=True,index=True)
    username=Column(String,unique=True)
    hashed_password = Column(String)