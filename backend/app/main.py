# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .db import create_db_and_tables
# Import routes
from .routes import user, auth, follow

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info("Starting up Morse-Me Backend...")
    try:
        create_db_and_tables()
        logger.info("Database tables created successfully!")
    except Exception as e:
        logger.error(f"Database error during startup: {e}")
        # App still starts, you can handle this gracefully

    yield  # App runs between startup and shutdown

    # Shutdown code
    logger.info("Shutting down Morse-Me Backend...")

app = FastAPI(
    title="Morse-Me Backend",
    description="Learn Morse Code, One Friend at a Time!",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware - allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.development_mode else settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(auth.router)

app.include_router(follow.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Morse-Me!", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": settings.app_name}