from datetime import datetime, timezone
from typing import List, cast

from fastapi import HTTPException,status
from sqlalchemy.orm import Session

from app.db.prep_db import PrepDB
from app.models.company import Company
from app.models.company_pages import CompanyPages
from app.models.user import User
from app.services.auth_services import AuthService
from app.services.prompt_service import PromptService
from app.services.scrape_service import get_scraped_data
from app.services.tos_extractor import get_tos_data
from app.utils.convert import company_page_to_dict




class InterviewPrep:

    @staticmethod
    async def site_complaince(url:str):
        tos_data = await get_tos_data(url)
        allow_scrape_tos = PromptService.tos_prompt(tos_data)
        return allow_scrape_tos



    @staticmethod
    async def create_prep(resume:str,url:str,job_desc:str,token:str,db:Session):
        payload=AuthService.verify_token(token,"access")
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unauthorised Access")
        pages_rows: List[CompanyPages] = []
        company = db.query(Company).filter(Company.url==url).first()
        print(payload)
        user = db.query(User).filter(User.user_id==payload.get("sub")).first()
        if user.credits<0:
            raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED,detail="You have run out of credits")
        if company is not None:
            pages_rows = cast(
                List[CompanyPages],
                db.query(CompanyPages).filter(CompanyPages.company_id == company.company_id).all()
            )

        else:
            allow_scrape_tos = await InterviewPrep.site_complaince(url)
            if allow_scrape_tos:
                scraped =await get_scraped_data(url)
                scraped_data = scraped.get("company_data",scraped)
                pages = scraped_data.get("pages",[])
                name_guess = scraped_data.get("company_name_guess")
                new_company = Company(url=url)
                new_company.name = name_guess
                new_company.image = scraped_data.get("favicon_url")
                db.add(new_company)
                db.commit()
                db.refresh(new_company)
                company = new_company
                now = datetime.now(timezone.utc).isoformat()
                for p in pages:
                    page_url = p.get("url")
                    if not page_url:
                        continue

                    exists=(
                        db.query(CompanyPages).filter(CompanyPages.company_id == new_company.company_id,
                    CompanyPages.page_url == page_url).first()
                    )
                    if exists:
                        continue
                    row = CompanyPages()
                    row.company_id=new_company.company_id
                    row.page_title=p.get("key")
                    row.page_url=page_url
                    row.page_content=p.get("text")
                    row.scraped_at=now
                    db.add(row)
                db.commit()

                pages_rows = cast(
                    List[CompanyPages],
                    db.query(CompanyPages)
                    .filter(CompanyPages.company_id == new_company.company_id)
                    .all()
                )

        company_data_clean = [company_page_to_dict(p) for p in pages_rows]
        prep_data = {"resume":resume,
            "company_data":company_data_clean,
            "job_description":job_desc}
        result = PromptService.create_prep_prompt(prep_data)
        created =datetime.now(timezone.utc).isoformat()
        PrepDB.interview_prep_save(payload.get("sub"),company.company_id,created,result,db)
        return result