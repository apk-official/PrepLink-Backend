from fastapi import HTTPException,status
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.company_pages import CompanyPages
from app.services.auth_services import AuthService
from app.services.tos_extractor import get_tos_data


class InterviewPrep:

    @staticmethod
    def site_complaince(url:str):
        tos_data = get_tos_data(url)



    @staticmethod
    def create_prep(resume:str,url:str,job_desc:str,token:str,db:Session):
        payload=AuthService.verify_token(token,"access")
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorised Access")
        company_data_exist= db.query(Company).filter(Company.url==url).first() is not None
        if company_data_exist:
            company=db.query(Company).filter(Company.url==url).first()
            company_data = db.query(CompanyPages).filter(CompanyPages.company_id==company.company_id)


        return {
            "resume":resume,
            "url":url,
            "job_desc":job_desc
        }