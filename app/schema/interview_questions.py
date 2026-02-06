from pydantic import BaseModel


class InterviewQuestions(BaseModel):
    question_id:int
    project_id:int
    question_type:str
    question:str
    answer:str