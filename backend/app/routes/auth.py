# routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlmodel import select
from datetime import timedelta

from ..core.security import (
    hash_password,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..dep import SessionDep
from ..models import Token, User, UserLogin, UserPublic, UserWithToken

router = APIRouter(prefix="/auth", tags=["authentication"])

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def authenticate_user(session, callsign: str, password: str):
    user = session.exec(
        select(User).where(User.callsign == callsign)
    ).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        session: SessionDep = Depends()
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        callsign: str = payload.get("sub")
        if callsign is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = session.exec(
        select(User).where(User.callsign == callsign)
    ).first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


@router.post(
    "/login",
    response_model=UserWithToken,
    summary="Login user",
    description="Authenticate user and return access token"
)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: SessionDep = Depends(),
):
    """
    Login endpoint that accepts username/password and returns JWT token.
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect callsign or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.callsign}, expires_delta=access_token_expires
    )

    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return UserWithToken(
        user=UserPublic.model_validate(user),
        token=token
    )


@router.post(
    "/login-json",
    response_model=UserWithToken,
    summary="Login user (JSON)",
    description="Authenticate user with JSON payload and return access token"
)
def login_json(
        user_login: UserLogin,
        session: SessionDep = Depends(),
):
    """
    Alternative login endpoint that accepts JSON payload.
    """
    user = authenticate_user(session, user_login.callsign, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect callsign or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.callsign}, expires_delta=access_token_expires
    )

    token = Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return UserWithToken(
        user=UserPublic.model_validate(user),
        token=token
    )


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    """
    return current_user


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh token",
    description="Refresh an existing access token"
)
def refresh_token(
        current_user: User = Depends(get_current_active_user)
):
    """
    Refresh access token for current user.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.callsign}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )