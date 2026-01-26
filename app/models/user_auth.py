from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import Mapped,mapped_column
from app.db.base import Base


class UserAuth(Base):
    __tablename__ = "user_auth"
    auth_id=Column(Integer,primary_key=True,index=True)
    user_id:Mapped[int]=mapped_column(Integer)
    email_id=Column(String)
    auth_method:Mapped[str]=mapped_column(String)
    provider_user_id=Column(String)
    refresh_token=Column(String)
    google_access_token=Column(String)
    google_refresh_token=Column(String)
    google_token_expiry=Column(DateTime)
    created_at=Column(String)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


