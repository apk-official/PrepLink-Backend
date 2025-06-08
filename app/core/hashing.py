from passlib.context import CryptContext

bcrypt_context = CryptContext(schemes=['bcrypt'],deprecated='auto')

def hash_password(password:str)->str:
    """
    Hash the plain text password using the bcrypt algorithm.

    Args:
        password (str): The plain text password provided by the user.

    Returns:
        str: The securely hashed version of the password.
    """
    return bcrypt_context.hash(password)

def verify_password(plain_password:str,hashed_password:str)->bool:
    """
    Verify plain text password matches with its hashed version.
    Args:
        plain_password(str): Original plain text password
        hashed_password(str): Hashed Password stored in Database
    Returns:
        bool: True if password match else False
    """
    return bcrypt_context.verify(plain_password,hashed_password)