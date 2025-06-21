# app/dep.py
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from .db import engine


def get_db_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection"""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db_session)]