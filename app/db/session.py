from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Construct the full Postgres database URL from environment variables
SQL_ALCHEMY_DATABASE_URL = settings.database_url

# Create the SQLAlchemy engine using the database URL
engine = create_engine(SQL_ALCHEMY_DATABASE_URL)
# Create a configured "SessionLocal" class
# Each instance will be a database session bound to the engine
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)