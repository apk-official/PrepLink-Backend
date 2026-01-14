from typing import Optional

from fastapi import Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.db.helper import get_db
from app.models.user import User


def get_or_create_user(
    db:Session,
    *,
    email: str,
    name: Optional[str] = None,
    img_url: Optional[str] = None,
    user_type: str = "tester",
    initial_credits: int = 5,) -> User:

    user =( db.query(User).filter(and_(User.email==email,User.disabled == False)).first())
    if user:
    # Optional: keep profile updated from Google on each login
        updated = False
        if name and user.name != name:
            user.name = name
            updated = True
        if img_url and user.img_url != img_url:
            user.img_url = img_url
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
        return user

    user = User(
        email=email,
        name=name,
        img_url=img_url,
        user_type=user_type,
        credits=initial_credits,
        disabled=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user