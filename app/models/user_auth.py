from sqlalchemy import Column, Integer, String, Boolean

from app.db.base import Base


class UserAuth(Base):
    __tablename__ = "user_auth"
    auth_id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer)
    email_id=Column(String)
    auth_method=Column(String)
    provider_user_id=Column(String)
    refresh_token=Column(String)
    created_at=Column(String)
