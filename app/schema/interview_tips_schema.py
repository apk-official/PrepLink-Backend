from pydantic import BaseModel


class InterviewTips(BaseModel):
    tip_id:int
    project_id:int
    tip:str