from collections.abc import Generator
from enum import Enum
from typing import Annotated, Optional

import sqlmodel
from fastapi import Depends
from pydantic import BaseModel, Field
from sqlmodel import Session, asc

from .db import engine


def get_db_session() -> Generator[Session, None, None]:
    """Get database session for dependency injection"""
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_db_session)]


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SearchQueryParams(BaseModel):
    q: str | None  = Field(None, description="Search query string")
    limit: int | None = Field(None, gt=0, description="limit the number of results")
    offset: int | None = Field(0, ge=0, description="skip the first n results")
    order_by: str | None = Field(SortOrder.DESC, description="Field to sort by")
    order: SortOrder | None = Field(SortOrder.DESC, description="Sort order")

SearchQueryParamsDep = Annotated[SearchQueryParams, Depends(SearchQueryParams)]
