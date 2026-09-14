"""Registration and JWT login endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a patient account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserRead:
    """Create a new patient user. Staff and admin accounts are created by admins."""
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = user_crud.create_user(
        db,
        UserCreate(
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=UserRole.PATIENT,
        ),
    )
    return user


@router.post("/login", response_model=TokenResponse, summary="Login and receive a JWT")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and return a signed access token."""
    user = user_crud.get_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    token = create_access_token(user.email, extra_claims={"role": user.role.value, "uid": user.id})
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        email=user.email,
    )


@router.post(
    "/login/form",
    response_model=TokenResponse,
    summary="OAuth2 password form login for Swagger",
    include_in_schema=True,
)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Accept username/password form so Swagger Authorize works."""
    return login(LoginRequest(email=form.username, password=form.password), db)
