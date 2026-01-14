from pydantic import BaseModel, EmailStr
from typing import Optional


class UserAuth(BaseModel):
    auth_id:int
    user_id :int
    email_id:Optional[EmailStr]=None
    auth_method:str
    access_token:str
    refresh_token:str
    disabled:str
    created_at:str