"""User administration and current-user endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import AdminUser, get_current_user
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserRead, summary="Current authenticated user")
def read_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the caller profile."""
    return current_user


@router.get("", response_model=list[UserRead], summary="List users (admin)")
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(AdminUser),
) -> list[User]:
    """List all users."""
    return user_crud.list_users(db, skip=skip, limit=limit)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user with a role (admin)",
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(AdminUser),
) -> User:
    """Create staff, doctor, patient, or admin accounts."""
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return user_crud.create_user(db, payload)


@router.patch("/{user_id}", response_model=UserRead, summary="Update a user (admin)")
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(AdminUser),
) -> User:
    """Update user fields."""
    user = user_crud.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_crud.update_user(db, user, payload)
