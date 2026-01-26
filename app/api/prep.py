from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException,status
from fastapi.params import Depends
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_access_token
from app.db.helper import get_db
from app.services.interview_prep_service import InterviewPrep
from app.utils.pdf_text_extractor import extract_text_from_pdf
from app.utils.url_validator import valid_base_url
router = APIRouter(prefix="/prep",tags=["interview-prep"])

@router.post("/")
async def interview_prep(resume:UploadFile=File(...), url:HttpUrl=Form(...), job_desc:str=Form(...),token:str=Depends(get_access_token),db:Session=Depends(get_db)):
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
    result = InterviewPrep.create_prep(resume_parsed,base_url,job_desc,token,db)
    return result