from pydantic import BaseModel


class Project(BaseModel):
    project_id:int
    user_id:int
    company_id:int
    position:str
    created_at:str