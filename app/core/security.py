from typing import Optional

from fastapi import HTTPException,status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from sqlalchemy import and_
from sqlalchemy.orm import Session
import jwt
from app.core.config import settings
from app.db.helper import get_db
from app.models.user import User

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/google")

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={
        "WWW-Authenticate": "Bearers"})
    try:
        payload=jwt.decode(token,settings.SECRET_KEY,algorithms=[settings.ALGORITHM],)
        email:Optional[str]=payload.get("sub")
        if email is None:
            raise credentials_exception
    except PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(and_(User.email==email,User.disabled == False)).first()
    if not user:
        raise credentials_exception

    return user

