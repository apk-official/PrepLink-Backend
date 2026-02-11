from fastapi import APIRouter, status, Request, HTTPException
from fastapi.params import Depends
from sqlalchemy.orm import Session

from app.core.deps import get_access_token
from app.core.ratelimit import limiter
from app.db.helper import get_db
from app.models.about_company import AboutCompany
from app.models.interview_question import InterviewQuestions
from app.models.interview_tips import InterviewTips
from app.models.project import Project
from app.models.user import User
from app.core.security import get_current_user
from app.models.user_auth import UserAuth
from app.services.auth_services import AuthService

router = APIRouter(prefix='/user', tags=['user'])

@router.get("/",status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
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

@router.delete("/{user_id}")
@limiter.limit("5/minute")
async def delete_user( user_id: int,
            token: str = Depends(get_access_token),
            db: Session = Depends(get_db)):
    payload = AuthService.verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Unauthorised Access")

    requester_id = payload.get("sub")
    if requester_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        project_ids = [
            pid for (pid,) in db.query(Project.project_id)
            .filter(Project.user_id == user_id)
            .all()
        ]

        if project_ids:
            db.query(InterviewQuestions).filter(
                InterviewQuestions.project_id.in_(project_ids)
            ).delete(synchronize_session=False)

            db.query(InterviewTips).filter(
                InterviewTips.project_id.in_(project_ids)
            ).delete(synchronize_session=False)

            db.query(AboutCompany).filter(
                AboutCompany.project_id.in_(project_ids)
            ).delete(synchronize_session=False)

            db.query(Project).filter(Project.project_id.in_(project_ids)).delete(
                synchronize_session=False
            )
        # 4) Delete auth row(s)
        db.query(UserAuth).filter(UserAuth.user_id == user_id).delete(synchronize_session=False)

        db.query(User).filter(User.user_id == user_id).delete(synchronize_session=False)

        db.commit()
        return None  # 204 No Content

    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")


