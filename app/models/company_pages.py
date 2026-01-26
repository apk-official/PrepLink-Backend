from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped,mapped_column


class CompanyPages:
    __tablename__="company_pages"
    page_id=Column(Integer,primary_key=True,index=True)
    company_id:Mapped[int]=mapped_column(Integer)
    page_title=Column(String)
    page_url=Column(String)
    page_content=Column(String)
    scraped_at=Column(String)

