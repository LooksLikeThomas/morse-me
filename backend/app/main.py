# app/main.py
import logging
from contextlib import asynccontextmanager
from select import select

from fastapi import FastAPI
from sqlmodel import Session
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .core.security import hash_password
from .db import create_db_and_tables, engine
from .models import User
# Import routes
from .routes import user, follow, login, channel

logger = logging.getLogger("uvicorn.error")

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    try:
        with Session(engine) as session:
            # Check if admin user already exists
            existing_admin = session.query(User).filter(User.callsign == "admin").first()

            if existing_admin:
                logger.info("Admin user already exists")
                return

            # Create default admin user
            admin_user = User(callsign="admin", hashed_password=hash_password("admin"))

            session.add(admin_user)
            session.commit()
            session.refresh(admin_user)

            logger.info(f"Default admin user created with ID: {admin_user.id}")

    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")


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

    create_default_admin()
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
app.include_router(login.router)
app.include_router(follow.router)
app.include_router(channel.router)

app.include_router(follow.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Morse-Me!", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": settings.app_name}