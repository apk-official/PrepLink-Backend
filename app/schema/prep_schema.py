from pydantic import BaseModel
from typing import List, Dict

class QAItem(BaseModel):
    question: str
    answer: str

class InterviewQA(BaseModel):
    General: List[QAItem]
    Technical: List[QAItem]
    Behavioural: List[QAItem]
    Other: List[QAItem]

class CompanyMission(BaseModel):
    content: str
    source_url: str

class AboutCompany(BaseModel):
    about:CompanyMission
    mission: CompanyMission
    vision: CompanyMission
    additional: CompanyMission

class TipItem(BaseModel):
    tip: str

class InterviewPrepResponse(BaseModel):
    job_position: str
    interview_qa: InterviewQA
    tips: List[TipItem]
    about_company: AboutCompany