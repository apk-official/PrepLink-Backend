import os
from datetime import timedelta

from sqlalchemy.orm import Session
from starlette import status
from typing import Annotated
from fastapi import Depends, Request, APIRouter, HTTPException
from authlib.integrations.starlette_client import OAuth
from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.helper import get_db
from app.models.user import User
from app.models.user_auth import UserAuth
from app.schema.auth_schema import TokenResponse, RefreshTokenRequest
from app.services.auth_services import AuthService
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter(prefix='/auth', tags=['auth'])

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope":"openid email profile"},
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    authorize_params={'access_type': 'offline', 'prompt': 'consent'}
)

# Initiate Google OAuth login
@router.get('/google')
@limiter.limit("5/minute")
async def auth_google(request:Request):
    redirect_uri=settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/google/callback')
@limiter.limit("5/minute")
async def google_callback(request:Request,db:Session=Depends(get_db)):
    # Handle Google OAuth callback
    try:
        token=await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to get user info")

        # Get or create user in database with Google tokens
        user = AuthService.get_or_create_user(
            db,
            user_info,
            google_refresh_token = token.get("refresh_token") or token.get("refresh"),
            google_access_token=token.get("access_token"),
            expires_in=token.get('expires_in',3600)
        )

        # Create own jwt token
        access_token_expiry=timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        access_token=AuthService.create_access_token(data={"sub":str(user.user_id),"email": user.email},
                                                     expires_delta=access_token_expiry)
        refresh_token = AuthService.create_refresh_token(data={"sub":str(user.user_id),"email": user.email})

        # Store refresh token in db

        AuthService.update_user_refresh_token(db,user.user_id,refresh_token)
        # Redirect to frontend with tokens
        redirect_url =settings.FRONTEND_URL
        return JSONResponse({
            "access_token":access_token,
            "refresh_token":refresh_token,
        })
    except Exception as e:
        print(f"Authentication error: {e}")
        redirect_url = f"{settings.FRONTEND_URL}"
        return RedirectResponse(url=redirect_url)



@router.post("/refresh",response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh_access_tokens(
        request:Request,
        refresh_request:RefreshTokenRequest,
        db: Session = Depends(get_db),
):
    """
    Refresh the access token using the refresh token.
    This endpoint should be called by the frontend when the access token expires.
    """
    # verify the request token
    payload = AuthService.verify_token(refresh_request.refresh_token,token_type="refresh")

    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Refresh Token")

    user_id = int(payload.get("sub"))

    # Verify user exists and is not disabled
    user = db.query(User).filter(User.user_id==user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="User account is disabled")

    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token=AuthService.create_access_token(
        data={"sub": str(user.user_id), "email": user.email},
        expires_delta=access_token_expires
    )

    new_refresh_token=AuthService.create_refresh_token(data={"sub": str(user.user_id), "email": user.email})

    # Update refresh token in database
    AuthService.update_user_refresh_token(db,user.user_id,new_refresh_token)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60
    )

@router.post("/logout")
@limiter.limit("5/minute")
async def logout(request:Request,refresh_request:RefreshTokenRequest,db:Session=Depends(get_db)):
    """Logout endpoint - invalidates refresh token"""
    payload = AuthService.verify_token(refresh_request.refresh_token,token_type="refresh")
    if payload:
        user_id=int(payload.get("sub"))
        user_auth=db.query(UserAuth).filter(UserAuth.user_id==user_id,
                                            UserAuth.auth_method=="google"
                                            ).first()
        if user_auth:
            user_auth.refresh_token=None
            db.commit()
    return {"message": "Logged out successfully"}

