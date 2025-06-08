
from app.core.hashing import verify_password
from app.models.user import Users

def authenticate_user(username:str,password:str,db):
    """
    Authenticate a user by verifying the provided username and password.

    Args:
        username (str): The username provided by the client.
        password (str): The plain-text password provided by the client.
        db (Session): SQLAlchemy database session.

    Returns:
        Users | bool: Returns the user object if authentication succeeds, else False.
    """
    user = db.query(Users).filter(Users.username==username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

