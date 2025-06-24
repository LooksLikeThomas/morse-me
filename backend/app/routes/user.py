# app/routes/user.py
import uuid
from typing import List

import bcrypt
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import func, select

from ..dep import SessionDep
from ..models import (
    User,
    UserCreate,
    UserPublic,
    UserPublicWithChannel,
    UserPublicDetailed,
)

router = APIRouter(prefix="/users", tags=["users"])


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


@router.post("/", response_model=UserPublic, status_code=201)
def create_user(user: UserCreate, session: SessionDep):
    """Register a new user"""
    # Check if callsign already exists
    existing_user = session.exec(
        select(User).where(User.callsign == user.callsign)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Callsign already registered"
        )

    # Create new user with hashed password
    db_user = User(
        callsign=user.callsign,
        hashed_password=hash_password(user.password)
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


@router.get("/", response_model=List[UserPublic])
def get_users(
        session: SessionDep,
        q: str | None = Query(None, description="Search query"),
        limit: int = Query(100, gt=0, le=1000),
        offset: int = Query(0, ge=0),
        order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Get list of users with optional search and pagination"""
    # Build query
    query = select(User)

    # Add search filter if provided
    if q:
        query = query.where(User.callsign.contains(q))

    # Get total count
    count_query = select(func.count()).select_from(User)
    if q:
        count_query = count_query.where(User.callsign.contains(q))
    total_count = session.exec(count_query).one()

    # Add ordering
    if order == "asc":
        query = query.order_by(User.callsign.asc())
    else:
        query = query.order_by(User.callsign.desc())

    # Add pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    users = session.exec(query).all()

    return users


@router.get("/{user_id}", response_model=UserPublicDetailed)
def get_user(user_id: uuid.UUID, session: SessionDep):
    """Get user by ID"""
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.get("/callsign/{callsign}", response_model=UserPublicDetailed)
def get_user_by_callsign(callsign: str, session: SessionDep):
    """Get user by callsign"""
    user = session.exec(
        select(User).where(User.callsign == callsign)
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user
