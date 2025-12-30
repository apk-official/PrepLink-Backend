from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.api import auth
from app.api import user
from app.api import interview_prep

# Create FastAPI app instance
app = FastAPI(
    title="Interview Prep API",
    version="1.0.0",
)

##API routers with versioned(v1) URL prefixes
app.include_router(auth.router,prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(interview_prep.router, prefix="/api/v1")

# Create database tables on startup (based on SQLAlchemy models)
Base.metadata.create_all(bind=engine)


