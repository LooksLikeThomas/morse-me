# app/dep.py
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from .db import get_db_session
from .models import User


# Import auth functions only when needed to avoid circular imports
def get_current_user_dep():
    """Lazy import to avoid circular dependency"""
    from .core.auth import get_current_user
    return get_current_user


def get_current_user_from_ws_dep():
    """Lazy import to avoid circular dependency"""
    from .core.auth import get_current_user_from_ws
    return get_current_user_from_ws

# Type aliases for cleaner code
SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user_dep())]
CurrentWsUser = Annotated[User, Depends(get_current_user_from_ws_dep())]