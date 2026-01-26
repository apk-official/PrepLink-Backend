from typing import Optional

from fastapi import HTTPException, status, Header


def get_access_token(authorization:Optional[str]=Header(None))->str:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Missing Authorization Header")
    parts = authorization.split()
    if len(parts)!=2 or parts[0].lower() !="bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization Header, Use Bearer <token>")
    return parts[1]