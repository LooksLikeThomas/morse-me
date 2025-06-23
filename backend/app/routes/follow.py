# app/routes/follow.py
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Response

from ..dep import SessionDep
from ..models import Follow, User, UsersPublic, UserPublic
from .auth import get_current_user

router = APIRouter(prefix="/follow", tags=["follow"])


@router.get(
    "/",
    response_model=UsersPublic,
    status_code=status.HTTP_200_OK
)
async def get_follows(
        session: SessionDep,
        current_user: User = Depends(get_current_user)
):
    """Get all users that current user follows"""
    user = session.get(User, current_user.id)
    return UsersPublic(data=user.follows, count=len(user.follows))


@router.post(
    "/{target_user_id}/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserPublic
)
async def follow_user(
        target_user_id: uuid.UUID,
        session: SessionDep,
        response: Response,
        current_user: User = Depends(get_current_user),
):
    """Follow a user by id"""

    target_user = session.get(User, target_user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot follow yourself"
        )

    # Already following that user
    if target_user in current_user.follows:
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return target_user

    # Create follow relationship
    follow = Follow(
        follower_id=current_user.id,
        followed_id=target_user.id
    )
    session.add(follow)
    session.commit()

    return target_user


@router.delete(
    "/{target_user_id}/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def unfollow_user(
        target_user_id: uuid.UUID,
        session: SessionDep,
        current_user: User = Depends(get_current_user)
):
    """Unfollow a user by id"""
    # Find target user
    target_user = session.get(User, target_user_id)

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    follow = session.get(Follow, (current_user.id, target_user.id))

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not following this user"
        )

    session.delete(follow)
    session.commit()

    return
