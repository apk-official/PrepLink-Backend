from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException,status
from fastapi.params import Depends
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_access_token
from app.core.ratelimit import limiter
from app.db.helper import get_db
from app.models.about_company import AboutCompany
from app.models.interview_question import InterviewQuestions
from app.models.interview_tips import InterviewTips
from app.models.project import Project
from app.models.user import User
from app.services.auth_services import AuthService
from app.services.interview_prep_service import InterviewPrep
from app.utils.pdf_text_extractor import extract_text_from_pdf
from app.utils.url import valid_base_url
router = APIRouter(prefix="/prep",tags=["interview-prep"])

@router.post("/")
@limiter.limit("5/minute")
async def interview_prep(request:Request,resume:UploadFile=File(...), url:HttpUrl=Form(...), job_desc:str=Form(...),token:str=Depends(get_access_token),db:Session=Depends(get_db)):
    if resume.content_type!="application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Only pdf files are allowed")
    size=0
    chunks:list[bytes]=[]

    while True:
        chunk = await resume.read(1024*1024)
        if not chunk:
            break
        size=+len(chunk)
        if size>settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="File size is too large(Max 7MB)")
        chunks.append(chunk)
    pdf_byte=b"".join(chunks)
    resume_parsed = extract_text_from_pdf(pdf_byte)
    base_url = valid_base_url(url)
    result =await InterviewPrep.create_prep(resume_parsed,base_url,job_desc,token,db)
    return result

@router.get("/")
@limiter.limit("5/minute")
def all_prep(request:Request,token:str=Depends(get_access_token),db:Session=Depends(get_db)):
    payload = AuthService.verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorised Access")
    projects = db.query(Project).filter(Project.user_id==payload.get("sub")).all()

    return projects


@router.get("/{prep_id}")
@limiter.limit("5/minute")
def get_prep(request:Request,prep_id:int,token:str=Depends(get_access_token),db:Session=Depends(get_db)):
    payload = AuthService.verify_token(token, "access")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorised Access")
    project = db.query(Project).filter(Project.project_id==prep_id).first()
    interview_question=db.query(InterviewQuestions).filter(InterviewQuestions.project_id==prep_id).all()
    tips=db.query(InterviewTips).filter(InterviewTips.project_id==prep_id).all()
    about_company=db.query(AboutCompany).filter(AboutCompany.project_id==prep_id).all()

    return {
            "interview_question":interview_question,
            "interview_tips":tips,
            "about_company":about_company
            }

