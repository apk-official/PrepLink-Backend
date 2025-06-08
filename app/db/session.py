from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQL_ALCHEMY_DATABASE_URL = "postgresql://postgres:apk123@localhost:5432/preplink"
engine = create_engine(SQL_ALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)