from pydantic import BaseModel


class InterviewQuestions(BaseModel):
    question_id:int
    project_id:int
    question_type:str
    answer:str