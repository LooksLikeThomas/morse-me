from sqlmodel import SQLModel, create_engine

from .config import settings  # type: ignore

# Create database engine
engine = create_engine(
    settings.database_url,
    echo=True,  # Set to False in production
    pool_pre_ping=True,  # Verify connections before use
)

def create_db_and_tables() -> None:
    """Create all database tables"""
    SQLModel.metadata.create_all(engine)
