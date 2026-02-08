from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.interview_question import InterviewQuestions
from app.models.project import Project


class PrepDB:
    @staticmethod
    def interview_prep_save(user_id:int,company_id,created_at,result,db:Session):
        company = db.query(Company).filter(Company.company_id==company_id).first()

        project = Project(
        user_id=user_id,
        company_id=company_id,
        position=getattr(result, "job_position", "unknown"),
        company_name=company.name,
        company_logo = company.image,
        created_at=created_at
        )
        db.add(project)
        db.commit()
        db.refresh(project)

        sections = {
            "General": result.interview_qa.General,
            "Technical": result.interview_qa.Technical,
            "Behavioural":result.interview_qa.Behavioural,
            "Other": result.interview_qa.Other,
        }

        for section_name, qa_list in sections.items():
            for qa in qa_list:
                db.add(
                    InterviewQuestions(
                        project_id=project.project_id,
                        question_type=section_name,
                        question=qa.question,
                        answer=qa.answer,
                    )
                )
        db.commit()
