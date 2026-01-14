import os
from datetime import timedelta, timezone, datetime
from typing import Optional

from fastapi import HTTPException,status

from app.core.config import settings
import jwt

from app.services.user_services import get_or_create_user


def create_access_token(data:dict,expires_delta:Optional[timedelta]=None,auth_method="google"):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    now = datetime.now(timezone.utc)
    to_encode.update({"exp": expire,"iat": now, "auth_method": auth_method})
    encoded_jwt=jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return encoded_jwt



async def google_authentication(request,oauth,db):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info=token.get("userinfo") or {}

        username=user_info.get("email")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google did not return an email",
            )

        # create user if missing (or update basic fields)
        user = get_or_create_user(db, email=email, name=name, img_url=picture)
        if not username:
            return {"error": "Google did not return an email"}

    # Generate a JWT token with auth_method="google"
        access_token = create_access_token(
            data={"sub":username},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            auth_method="google"
        )
        return {"access_token":access_token,"token":token}
    except Exception as e:
        import traceback
        print("Error:",traceback.format_exc())
        return {"error":str(e)}
