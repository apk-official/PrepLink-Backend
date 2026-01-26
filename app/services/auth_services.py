
import secrets
from datetime import timedelta, timezone, datetime
from typing import Optional
import httpx
from fastapi import HTTPException,status
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import Session
from app.core.config import settings
import jwt
from app.models.user import User
from app.models.user_auth import UserAuth



class AuthService:
    @staticmethod
    def create_access_token(data:dict,expires_delta:Optional[timedelta]=None):
        """Create short-lived access token"""
        to_encode=data.copy()
        if expires_delta:
            expire=datetime.now(timezone.utc)+expires_delta
        else:
            expire=datetime.now(timezone.utc)+timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        print("ACCESS_TOKEN_EXPIRE_MINUTES (runtime) =", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        now = datetime.now(timezone.utc)
        to_encode.update({"exp":expire,"iat": now,"type":"access"})
        encoded_jwt=jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data:dict):
        """Create long-lived refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp":expire,
            "type":"refresh",
            "jti":secrets.token_urlsafe(32)
        })
        encoded_jwt=jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token:str,token_type:str="access"):
        """Verify JWT token and access type"""
        try:
            payload=jwt.decode(token,settings.SECRET_KEY,algorithms=settings.ALGORITHM)
            if payload.get("type")!=token_type:
                return None
            return payload
        except ExpiredSignatureError:
            return None
        except InvalidTokenError:
            return None

    @staticmethod
    async def refresh_google_access_token(google_refresh_token:str):
        """Use Googles refresh token to get a new access token"""
        try:
            async with httpx.AsyncClient as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id":settings.GOOGLE_CLIENT_ID,
                        "client_secret":settings.GOOGLE_CLIENT_SECRET,
                        "refresh_token":google_refresh_token,
                        "grant_type":"refresh_token"
                    }
                )
                if response.status_code==200:
                    token_data=response.json()
                    return{
                        "access_token":token_data.get("access_token"),
                        "expires_in":token_data.get("expires_in",3600)
                    }
                return None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to refresh Google authentication token"
            )

    @staticmethod
    def get_or_create_user(
            db:Session,
            google_user_info:dict,
            google_refresh_token:Optional[str]=None,
            google_access_token:Optional[str]=None,
            expires_in:int=3600
    ):
        """Get existing user or create new user from Google profile"""
        email=google_user_info.get("email")
        google_id=google_user_info.get("sub")

       # Check if user exist
        user=db.query(User).filter(User.email==email).first()

        if not user:
            # Create New User
            user=User(
                name=google_user_info.get("name",""),
                email=email,
                user_type="tester",
                img_url=google_user_info.get("picture",""),
                disabled=False,
                credits=5
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            #update user info if changed
            user.name=google_user_info.get("name", user.name)
            user.img_url=google_user_info.get("picture",user.img_url)

        # Check if auth record exists
        user_auth=db.query(UserAuth).filter(
            UserAuth.user_id==user.user_id,
            UserAuth.auth_method=="google"
        ).first()

        token_expiry = datetime.now()+timedelta(seconds=expires_in)

        if not user_auth:
            user_auth=UserAuth(
                user_id=user.user_id,
                email_id =user.email,
                auth_method="google",
                provider_user_id =google_id,
                google_access_token =google_access_token,
                google_refresh_token=google_refresh_token,
                google_token_expiry=token_expiry,
                created_at=datetime.now().isoformat()
            )
            db.add(user_auth)
        else:
            # Update Tokens
            if google_refresh_token:
                user_auth.google_refresh_token = google_refresh_token
            if google_access_token:
                user_auth.google_access_token = google_access_token
                user_auth.google_token_expiry=token_expiry
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_user_refresh_token(db:Session,user_id:int,refresh_token:str):
        """Update user's JWT refresh token in database"""
        user_auth = db.query(UserAuth).filter(
            UserAuth.user_id==user_id,
            UserAuth.auth_method=="google"
        ).first()
        if user_auth:
            user_auth.refresh_token=refresh_token
            db.commit()
