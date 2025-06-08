from http.client import HTTPException
from fastapi import HTTPException
from jose import jwt,JWTError
from datetime import timedelta, datetime
from starlette import status
from app.core.config import settings

#Secret key & algorithm used for JWT encoding/decoding
SECRET_KEY =settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def create_access_token(username:str,user_id:int,expires_delta:timedelta):
    """
    Create a JWT access token with an expiration time.
    Args:
        username(str): Username of authenticated user
        user_id(int): Unique user id
        expires_delta(int): Duration after which the token will expire.
    Returns:
        str: Encoded JWT token as a string.
    """
    encode = {'sub':username, 'id': user_id}
    expires = datetime.now()+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode, SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str):
    """
       Decode a JWT token & extract payload
       Args:
           token(str): JWT token sent by client
       Raise:
            HTTPException: If JWT Token is expired or invalid
       Returns:
           dict: Decoded payload from JWT Token
       """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate Credentials',
                            )

