from fastapi import APIRouter, UploadFile, File, Form,HTTPException,status,Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from pydantic import HttpUrl,TypeAdapter

from app.schemas.scrape import ScrapeRequest
from app.services.interview_prep_service import interview_prep

router = APIRouter(
    prefix="/interview-prep",
    tags=['interview question']
)

# OAuth2 bearer token scheme setup with login path
oauth2bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


@router.post("/",status_code=status.HTTP_200_OK)
async def interview_prep_data(
        company_url:Annotated[str,Form()],
        job_desc:Annotated[str,Form()],
        resume:Annotated[UploadFile,File()],
        token:Annotated[str, Depends(oauth2bearer)]):
    try:
        # validate the URL format using your Pydantic model
        http_url = TypeAdapter(HttpUrl).validate_python(company_url)
        validated_url:HttpUrl = ScrapeRequest(url=http_url).url
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid URL: {e}")

    return await interview_prep(str(validated_url),resume,job_desc,token)