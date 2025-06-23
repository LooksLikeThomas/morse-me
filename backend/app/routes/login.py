import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import select

from ..config import settings
from ..core.auth import get_current_user, verify_password
from ..core.security import create_access_token
from ..dep import SessionDep
from ..models import (
    LoginRequest,
    TokenResponse,
    User,
    UserPublicDetailed,
    UserPublic,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Routes
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest, session: SessionDep):
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


@router.get("/me", response_model=UserPublicDetailed)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user