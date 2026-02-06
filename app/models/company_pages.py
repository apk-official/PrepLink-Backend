from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped,mapped_column

from app.db.base import Base


class CompanyPages(Base):
    __tablename__="company_pages"
    page_id:Mapped[int]=mapped_column(Integer,primary_key=True,index=True)
    company_id:Mapped[int]=mapped_column(Integer)
    page_title:Mapped[str]=mapped_column(String)
    page_url:Mapped[str]=mapped_column(String)
    page_content:Mapped[str]=mapped_column(String)
    scraped_at:Mapped[str]=mapped_column(String)

