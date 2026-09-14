"""User CRUD operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_by_id(db: Session, user_id: int) -> User | None:
    """Fetch a user by primary key."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by unique email."""
    stmt = select(User).where(User.email == email.lower())
    return db.execute(stmt).scalar_one_or_none()


def list_users(db: Session, skip: int = 0, limit: int = 50) -> list[User]:
    """Return a page of users."""
    stmt = select(User).offset(skip).limit(limit).order_by(User.id)
    return list(db.execute(stmt).scalars().all())


def create_user(db: Session, payload: UserCreate) -> User:
    """Create a user with a hashed password."""
    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_superuser(
    db: Session,
    email: str,
    password: str,
    full_name: str,
) -> User:
    """Create or return the bootstrap admin user."""
    existing = get_by_email(db, email)
    if existing:
        return existing
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    """Apply a partial update to a user."""
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for key, value in data.items():
        setattr(user, key, value)
    if password:
        user.hashed_password = hash_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
