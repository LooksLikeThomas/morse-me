# tests/conftest.py
"""Shared test fixtures and configuration"""
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.dep import get_db_session
from app.main import app


@pytest.fixture(scope="function")
def session():
    """Create a fresh test database session for each test"""
    engine = create_engine(
        "sqlite:///",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    # Clean up after each test
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(session: Session):
    """Create test client with dependency override"""
    def get_session_override():
        return session

    app.dependency_overrides[get_db_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()