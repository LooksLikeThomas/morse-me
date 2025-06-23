# app/core/auth.py
import datetime
from uuid import UUID

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select
from starlette.websockets import WebSocket

from ..db import get_db_session
from ..models import LoginRequest, TokenResponse, User, UserPublic
from .security import create_access_token, decode_token

# Create router for auth endpoints
router = APIRouter(prefix="/auth", tags=["auth"])

# Security
security = HTTPBearer()


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# Dependency to get current user
async def get_current_user(
        session: Session = Depends(get_db_session),
        credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get the current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Convert string to UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )

    user = session.get(User, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Update last_seen timestamp
    user.last_seen = datetime.datetime.utcnow()
    session.add(user)
    session.commit()

    return user


async def get_current_user_from_ws(
        websocket: WebSocket,
        session: Session = Depends(get_db_session),
        token: str | None = Query(None)
) -> User | None:
    """
    Dependency to get the current user from a WebSocket connection.
    Reads the token from query parameters.
    """
    if token is None:
        # 1008: Policy Violation
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return None

    try:
        payload = decode_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return None

    user_id = payload.get("sub")

    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid user ID format")
        return None

    user = session.get(User, user_uuid)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User not found")
        return None

    # Update last_seen timestamp
    user.last_seen = datetime.datetime.utcnow()
    session.add(user)
    session.commit()

    return user


# Auth Routes
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, session: Session = Depends(get_db_session)):
    """Login with callsign and password"""
    # Find user by callsign
    user = session.exec(
        select(User).where(User.callsign == login_data.callsign)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect callsign or password"
        )

    # Create token with user ID as subject
    access_token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        user=UserPublic.model_validate(user)
    )


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
