
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from app.models.user import Users
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.api.deps import get_db
from app.core.hashing import hash_password, verify_password
from app.schemas.user import CreateUserRequest
from app.schemas.token import Token
from datetime import timedelta, datetime
from app.core.security import create_access_token, decode_access_token

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)


oauth2bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,create_user_request: CreateUserRequest):
    create_user_model = Users(username=create_user_request.username,
                              hashed_password=hash_password(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()

@router.post("/token",response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user.')
    token = create_access_token(user.username,user.id,timedelta(minutes=20))

    return {'access_token':token,'token_type':'bearer'}

def authenticate_user(username:str,password:str,db):
    user = db.query(Users).filter(Users.username==username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

async def get_current_user(token:Annotated[str, Depends(OAuth2PasswordBearer)]):
    payload = decode_access_token(token)
    username:str = payload.get('sub')
    user_id:int = payload.get('id')
    if username is None or user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could Not Validate User')
    return {'username':username,'id':user_id}
