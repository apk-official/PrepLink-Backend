from pydantic import BaseModel

class CreateUserRequest(BaseModel):
    """
        Schema for incoming user registration request.

        Attributes:
            username (str): Desired username of the user.
            password (str): Plain text password to be hashed before saving.
    """
    username:str
    password:str

class UserOut(BaseModel):
    """
        Schema for user data returned in API responses.

        Attributes:
            username (str): The registered username.
            id (int): The hashed password (not typically returned — consider omitting).
     """
    username:str
    id:int
    model_config = {
        "from_attributes": True
    }
