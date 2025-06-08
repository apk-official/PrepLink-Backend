from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    username:str
    password:str

class UserOut(BaseModel):
    username:str
    password:str
    model_config = {
        "from_attributes": True
    }
