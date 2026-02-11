from fastapi import HTTPException,status
from sqlalchemy.orm import Session

from app.models.about_company import AboutCompany
from app.models.company import Company
from app.models.interview_question import InterviewQuestions
from app.models.interview_tips import InterviewTips
from app.models.project import Project
from app.models.user import User


class InvalidDataException(Exception):
    """Raised when the AI result is empty/invalid."""

def _looks_invalid(value) -> bool:
    """
    Returns True if value is:
    - None / empty string / empty list / empty dict
    - OR contains the text "invalid data" (case-insensitive)
    """
    if value is None:
        return True

    # String
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return True
        if "invalid data" in s.lower():
            return True
        return False

    # List / tuple / set
    if isinstance(value, (list, tuple, set)):
        if len(value) == 0:
            return True
        # if any element is literally/contains "invalid data", treat as invalid
        return any(_looks_invalid(v) for v in value)

    # Dict
    if isinstance(value, dict):
        if len(value) == 0:
            return True
        return any(_looks_invalid(v) for v in value.values())

    return False



class PrepDB:
    @staticmethod
    def interview_prep_save(user_id:int,company_id,created_at,result,db:Session):
        try:
            # -------- 1) Validate sections (General/Technical/Behavioural/Other) --------
            interview_qa = getattr(result, "interview_qa", None)
            if _looks_invalid(interview_qa):
                raise InvalidDataException("invalid data")

            sections = {
                "General": getattr(interview_qa, "General", None),
                "Technical": getattr(interview_qa, "Technical", None),
                "Behavioural": getattr(interview_qa, "Behavioural", None),
                "Other": getattr(interview_qa, "Other", None),
            }

            # Edge case: if ANY section list is missing or empty -> invalid
            for section_name, qa_list in sections.items():
                if qa_list is None or not isinstance(qa_list, list) or len(qa_list) == 0:
                    raise InvalidDataException("invalid data")

                for qa in qa_list:
                    q = getattr(qa, "question", None)
                    a = getattr(qa, "answer", None)

                    if _looks_invalid(q) or _looks_invalid(a):
                        raise InvalidDataException("invalid data")

            # -------- 2) Validate tips --------
            tips = getattr(result, "tips", None)
            if _looks_invalid(tips):
                raise InvalidDataException("invalid data")

            # -------- 3) Validate about_company --------
            about_company = getattr(result, "about_company", None)
            if _looks_invalid(about_company):
                raise InvalidDataException("invalid data")

                # -------- If all validations pass, then save --------
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
            for tip in result.tips:
                db.add(InterviewTips(
                    project_id=project.project_id,
                    tip=tip.tip
            ))
            db.commit()
            db.add(AboutCompany(
                project_id=project.project_id,
                vision=result.about_company.vision.content,
                vision_url=result.about_company.vision.source_url,
                mission=result.about_company.mission.content,
                mission_url=result.about_company.mission.source_url,
                additional=result.about_company.additional.content,
                additional_url=result.about_company.additional.source_url,
            ))
            db.commit()
            user=db.query(User).filter(User.user_id==user_id).first()
            user.credits=user.credits-1
            db.commit()
            db.refresh(user)
        except InvalidDataException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise