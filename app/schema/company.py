from pydantic import BaseModel


class Company(BaseModel):
    company_id:int
    name:str
    url:str
    title:str
    desc:str