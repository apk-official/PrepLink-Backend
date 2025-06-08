from http.client import HTTPException
from fastapi import HTTPException
from jose import jwt,JWTError
from datetime import timedelta, datetime
from starlette import status
from app.core.config import settings

SECRET_KEY =settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def create_access_token(username:str,user_id:int,expires_delta:timedelta):
    encode = {'sub':username, 'id': user_id}
    expires = datetime.now()+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode, SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate Credentials',
                            )

