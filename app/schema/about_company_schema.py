from pydantic import BaseModel


class AboutCompany(BaseModel):
    about_company_id:int
    project_id:int
    vision:str
    mission:str
    additional:str