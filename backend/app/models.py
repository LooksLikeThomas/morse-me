import uuid
from typing import Generic, TypeVar

import fastapi.exceptions
from sqlmodel import Field, SQLModel

# Generic type variable
DataT = TypeVar('DataT')

class ApiResponse(SQLModel, Generic[DataT]):
    """Unified API response model."""
    data: DataT | None
    error: str | None

# Shared properties
class UserBase(SQLModel):
    callsign: str = Field(unique=True, index=True, max_length=255)

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str

# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
