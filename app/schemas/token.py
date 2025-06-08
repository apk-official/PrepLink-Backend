from pydantic import BaseModel

class Token(BaseModel):
    """
    Pydantic schema for representing a JWT access token response.

    Attributes:
        access_token (str): The JWT token string returned after authentication.
        token_type (str): The type of the token, typically 'bearer'.
    """
    access_token: str
    token_type: str