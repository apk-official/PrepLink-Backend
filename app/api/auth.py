import os

from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from fastapi import Depends, Request, APIRouter, HTTPException
from authlib.integrations.starlette_client import OAuth
from app.core.deps import get_settings
from app.core.config import settings
from app.db.helper import get_db
from app.services.auth_services import google_authentication, create_access_token
from app.services.user_services import get_or_create_user

router = APIRouter(prefix='/auth', tags=['auth'])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope":"openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration"
)

# Redirect user to Google for authentication
@router.get('/google')
async def auth_google(request:Request):
    return await oauth.google.authorize_redirect(request, redirect_uri="http://localhost:8000/api/v1/auth/google/callback")


@router.get('/google/callback')
async def google_callback(request:Request,db:Session=Depends(get_db)):
    info = await google_authentication(request, oauth)
    if "error" in info:
        raise HTTPException(status_code=400, detail=info["error"])

    user = get_or_create_user(db, email=info["email"], name=info["name"], img_url=info["picture"])

    access_token = create_access_token(data={"sub": user.email}, auth_method="google")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "user_type": user.user_type,
            "img_url": user.img_url,
            "credits": user.credits,
            "disabled": user.disabled,
        },
    }
