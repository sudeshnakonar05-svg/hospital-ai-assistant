"""Unit tests for bcrypt hashing and JWT signing."""

from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    try_decode_access_token,
    verify_password,
)


def test_password_hashing_and_verification() -> None:
    """bcrypt hashes verify the original password and reject a wrong one."""
    raw_pwd = "SecretHospitalPassword123!"
    hashed = hash_password(raw_pwd)
    assert hashed != raw_pwd
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_creation_and_decoding() -> None:
    """JWT tokens are signed and decoded with role and sub claims."""
    settings = get_settings()
    email = "doctor@hospital.local"
    token = create_access_token(email, extra_claims={"role": "doctor"})

    payload = decode_access_token(token)
    assert payload["sub"] == email
    assert payload["role"] == "doctor"
    assert "exp" in payload


def test_invalid_jwt_rejected() -> None:
    """A token signed with the wrong secret is rejected by decoding."""
    token = jwt.encode({"sub": "fraud@hospital.local"}, "wrong-secret-key-12345678", algorithm="HS256")
    assert try_decode_access_token(token) is None
