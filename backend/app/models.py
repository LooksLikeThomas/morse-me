# app/models.py
import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


# User Models
class UserBase(SQLModel):
    callsign: str = Field(unique=True, index=True, max_length=255, min_length=3)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int