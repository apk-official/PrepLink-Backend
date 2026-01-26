from fastapi import APIRouter, status, Request, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.db.helper import get_db
from app.models.user import User
from app.core.security import get_current_user
from app.services.auth_services import AuthService

router = APIRouter(prefix='/user', tags=['user'])

@router.get("/",status_code=status.HTTP_200_OK)
async def user(request:Request,db:Session=Depends(get_db)):
    """Get current user information"""
    auth_header=request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Not Authenticated")
    token = auth_header.split(" ")[1]
    payload = AuthService.verify_token(token,token_type="access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid or Expired token.Please Refresh")
    user_id=int(payload.get("sub"))
    user=db.query(User).filter(User.user_id==user_id).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    if user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User is disabled")
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "user_type": user.user_type,
        "img_url": user.img_url,
        "credits": user.credits
    }