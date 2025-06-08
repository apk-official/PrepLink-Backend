from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from app.core.security import decode_access_token

# OAuth2 bearer token scheme setup with login path
oauth2bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

# Dependency function to extract current user from the JWT token
async def get_current_user(token:Annotated[str, Depends(oauth2bearer)]):
    """
    Decode and validate the JWT token from the Authorisation header.
    This is a reusable dependency used to get the current user.

    Raises:
        HTTPException: If the token is invalid or missing necessary user data.

    Returns:
        dict: The payload containing username and user_id.
    """
    payload = decode_access_token(token)
    username:str = payload.get('sub')
    user_id:int = payload.get('id')
    if username is None or user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could Not Validate User')
    return {'username':username,'id':user_id}