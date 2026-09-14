"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    """Credentials for JWT login."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """JWT access token payload."""

    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    email: EmailStr


class RegisterRequest(BaseModel):
    """Public registration payload. New users default to patient role."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=255)
