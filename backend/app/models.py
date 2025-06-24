# app/models.py
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Literal, List, Optional

from pydantic import BaseModel, computed_field
from sqlmodel import Field, Relationship, SQLModel

# Channel Models
class ChannelPublic(BaseModel):
    """Public representation of a channel"""
    channel_id: str
    users: list["UserPublic"] = Field(default_factory=list)
    is_full: bool
    created_at: datetime


class ChannelsPublic(BaseModel):
    """List of channels"""
    channels: list[ChannelPublic]
    count: int


# Follow Models
class Follow(SQLModel, table=True):
    """Follow relationship table"""
    follower_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    followed_id: uuid.UUID = Field(foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    follower: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "Follow.follower_id",
            "viewonly": True
        }
    )
    followed: "User" = Relationship(
        sa_relationship_kwargs={
            "foreign_keys": "Follow.followed_id",
            "viewonly": True
        }
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
    last_seen: datetime = Field(default_factory=datetime.utcnow)

    @computed_field  # type: ignore
    @property
    def status(self) -> Literal["online", "offline", "waiting", "busy"]:
        if (
                not self.last_seen
                or (datetime.utcnow() - self.last_seen).total_seconds() > 600
        ):
            return "offline"

        # Lazy import to avoid circular dependency
        from .core.connection_manager import manager

        # Check if user is in a channel
        channel = manager.get_user_channel(self.id)
        if channel:
            if channel.is_full:
                return "busy"
            else:
                return "waiting"

        return "online"

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


class UserPublic(UserBase):
    """Basic user model without follow data"""
    id: uuid.UUID
    created_at: datetime
    last_seen: Optional[datetime] = None
    status: Literal["online", "offline", "waiting", "busy"] = "offline"


class UserPublicWithChannel(UserPublic):
    """User model with channel data"""
    in_channel: Optional[str] = None


class UserPublicWithFollowers(UserPublic):
    """User model with full follow/follower data"""
    follows: List[UserPublic] = []
    followers: List[UserPublic] = []


class UserPublicDetailed(UserPublicWithFollowers, UserPublicWithChannel):
    """User model completely"""
    pass



# Auth Models
class LoginRequest(BaseModel):
    callsign: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic