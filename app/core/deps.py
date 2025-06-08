from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

def get_db()-> Generator[Session,None,None]:
    """
    Yields a database session using SQLAlchemy.

    This function is a dependency used to inject a database session
    into path operations. It ensures the session is opened and closed properly.

    Yields:
        Session: An active SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
