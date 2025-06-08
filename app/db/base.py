from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
        Base class for all SQLAlchemy models.

        This class is used as the base for defining ORM models.
        All model classes should inherit from this Base class to gain
        SQLAlchemy's ORM capabilities.
        """
    pass
