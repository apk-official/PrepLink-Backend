
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.deps import get_db

from app.schemas.token import Token
from datetime import timedelta
from app.core.security import create_access_token
from app.core.config import settings
from app.services.auth_service import authenticate_user

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/token",response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    """
    Authenticate the user and generate a JWT access token.

    This endpoint is used to log in a user with their username and password.
    It validates the credentials and returns a bearer token used for future authenticated requests.

    Args:
        form_data (OAuth2PasswordRequestForm): Contains the username and password provided by the client.
        db (Session): SQLAlchemy database session dependency.

    Raises:
        HTTPException: If authentication fails due to invalid credentials.

    Returns:
        dict: A dictionary with 'access_token' and 'token_type'.
    """
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(user.username,user.id,timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    return {'access_token':token,'token_type':'bearer'}

