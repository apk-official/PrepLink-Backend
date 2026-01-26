

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.prep import router as prep_router
from app.core.config import settings
from app.db.base import Base
from app.db.sessions import engine

app = FastAPI(title="PrepLink", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


##API routers with versioned(v1) URL prefixes
app.include_router(auth_router,prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(prep_router, prefix="/api/v1")


# Create database tables on startup (based on SQLAlchemy models)
Base.metadata.create_all(bind=engine)