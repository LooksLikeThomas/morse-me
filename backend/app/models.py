# app/models.py
import uuid
from datetime import datetime
from typing import List

from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Relationship


# Follow Models
class Follow(SQLModel, table=True):
    """Follow relationship table"""

    follower_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    followed_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    follower: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "Follow.follower_id",
            "viewonly": "True"
        }
    )
    followed: "User" = Relationship(
        sa_relationship_kwargs=dict(
            foreign_keys="Follow.followed_id",
            viewonly=True)
    )

# User Models
class UserBase(SQLModel):
    callsign: str = Field(unique=True, index=True, max_length=255, min_length=3)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    follows: List["User"] = Relationship(
        link_model=Follow,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Follow.follower_id",
            "secondaryjoin": "User.id==Follow.followed_id",
            "overlaps": "followers",
        },
    )

    # Users that follow this user
    followers: List["User"] = Relationship(
        link_model=Follow,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==Follow.followed_id",
            "secondaryjoin": "User.id==Follow.follower_id",
            "overlaps": "follows",
        },
    )


class UserPublicFlat(UserBase):
    """User model with only IDs for follows/followers to avoid recursion"""
    id: uuid.UUID
    created_at: datetime


class UserPublic(UserBase):
    """User model with full follow/follower data"""
    id: uuid.UUID
    created_at: datetime
    follows: List[UserPublicFlat] = []
    followers: List[UserPublicFlat] = []


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Auth Models
class LoginRequest(BaseModel):
    callsign: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublicFlat