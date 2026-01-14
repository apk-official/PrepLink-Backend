from pydantic import BaseModel, EmailStr


class User(BaseModel):
    user_id:int
    name:str
    email:EmailStr
    user_type:str
    img_url:str
    credits:int