

from dotenv import load_dotenv
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth import router as auth_router
from app.api.user import router as user_router
from app.api.prep import router as prep_router
from app.core.config import settings
from app.db.base import Base
from app.db.sessions import engine
from app.core.ratelimit import limiter
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PrepLink", version="1.0.0",redirect_slashes=False)

app.state.limiter = limiter
app.add_middleware(SessionMiddleware,
                   secret_key=settings.SECRET_KEY,
                   same_site="lax",  # or "none" if cross-site issues
                   https_only=True,
                   )
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
origins = [
    "https://app.preplinkapp.com"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],      # or ["GET","POST","PUT","DELETE"]
    allow_headers=["*"],      # includes Authorization
)

##API routers with versioned(v1) URL prefixes
app.include_router(auth_router,prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(prep_router, prefix="/api/v1")


# Create database tables on startup (based on SQLAlchemy models)
Base.metadata.create_all(bind=engine)