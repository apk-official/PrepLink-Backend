from fastapi import APIRouter, HTTPException, Depends, status
from typing import Annotated
from app.core.deps import get_db
from sqlalchemy.orm import Session
from app.services.user_service import get_current_user
from app.schemas.user import UserOut
from app.core.hashing import hash_password
from app.schemas.user import CreateUserRequest
from app.models.user import Users

router = APIRouter(
    prefix="/user",
    tags=['user']
)

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,create_user_request: CreateUserRequest):
    """
    Register a new user account.

    Hashes the password and stores the new user in the database.

    Args:
        db (Session): SQLAlchemy database session.
        create_user_request (CreateUserRequest): Payload containing username and password.

    Returns:
        None
    """
    create_user_model = Users(username=create_user_request.username,
                              hashed_password=hash_password(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()

@router.get("/",status_code=status.HTTP_200_OK,response_model=UserOut)
async def user(current_user: user_dependency,db:db_dependency):
    """
        Retrieve the authenticated user's profile.

        Requires a valid JWT token in the Authorisation header.

        Args:
            current_user (dict): The current authenticated user extracted from the JWT token.
            db (Session): SQLAlchemy database session.

        Raises:
            HTTPException: If authentication fails.

        Returns:
            dict: The current user info (id, username) using UserOut schema.
        """
    if current_user is None:
        raise HTTPException(status_code=401,detail='Authentication Failed')
    return current_user