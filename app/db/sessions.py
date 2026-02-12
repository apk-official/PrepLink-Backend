from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

SQL_ALCHEMY_DATABASE_URL=settings.database_url

engine=create_engine(SQL_ALCHEMY_DATABASE_URL,connect_args={
        "sslmode": "verify-full",
        "sslrootcert": "/certs/global-bundle.pem",
    },)

SessionLocal=sessionmaker(autocommit=False, autoflush=False,bind=engine)