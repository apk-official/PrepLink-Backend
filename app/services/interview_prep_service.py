from fastapi import HTTPException,status, UploadFile
from typing import Annotated
from app.services.scrape_service import get_scraped_data
from app.utils.pdf_text_extractor import extract_text_from_pdf
from app.core.security import decode_access_token

async def interview_prep(url:str,resume:UploadFile,job_desc:str,token:str):
    try:
        if not url.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="URL cannot be empty or whitespace.")
        payload = decode_access_token(token)
        if not payload.get("sub") or not payload.get("id"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could Not Validate User")

        #Exctracting resume contents using utility functions
        resume_bytes = await resume.read()
        resume_text = extract_text_from_pdf(resume_bytes)

        #Scraping Data from Company URL
        scraped_data = await get_scraped_data(url,token)
        # "Pdf_Data": resume_text,
        return {"Scraped_Data":scraped_data,"Resume_data":resume_text,"Job_Desc":job_desc}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500,detail="Failed Generating Interview Data")

