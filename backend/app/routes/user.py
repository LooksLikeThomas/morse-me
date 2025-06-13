from fastapi import APIRouter, HTTPException
from sqlmodel import select, col

from ..dep import SessionDep, SearchQueryParams, SearchQueryParamsDep, SortOrder  # type: ignore
from ..models import User, UsersPublic  # type: ignore

router = APIRouter(prefix="/users", tags=["users"])

from sqlalchemy import func, asc, desc


@router.get(
    "/",
    response_model=UsersPublic,
)
def get_users(
    session: SessionDep,
    params: SearchQueryParamsDep,
):
    """
    Retrieve users.
    """

    try:
        # Base query
        query = select(User)

        # Apply search filter
        if params.q:
            query = query.where(col(User.callsign).ilike(f"%{params.q}%"))

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_count = session.exec(count_query).one()

        # Order by query param, default to callsign
        if params.order_by:
            order_column = getattr(User, params.order_by, User.callsign)
        else:
            order_column = User.callsign

        # Sort Order
        if params.order == SortOrder.ASC:
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))

        # Apply pagination
        query = query.offset(params.offset)
        query = query.limit(params.limit)

        # Exec Query
        users = session.exec(query).all()

        return UsersPublic(data=users, count=total_count)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error retrieving users")
