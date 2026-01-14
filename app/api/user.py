from fastapi import APIRouter, status
from fastapi.params import Depends
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(prefix='/user', tags=['user'])

@router.get("/",status_code=status.HTTP_200_OK)
async def user(current_user:User=Depends(get_current_user)):
    return {"user_id": current_user.user_id,
    "name": current_user.name,
    "email": current_user.email,
    "user_type": current_user.user_type,
    "img_url": current_user.img_url,
    "credits": current_user.credits,
    "disabled": current_user.disabled,}