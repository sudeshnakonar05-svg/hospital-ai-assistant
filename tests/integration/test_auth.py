"""Integration tests for Authentication (Register, Login, Protected Endpoint, Invalid Token)."""

from fastapi.testclient import TestClient


def test_auth_registration_workflow(client: TestClient) -> None:
    """Users can register a new account."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New Assistant User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New Assistant User"
    assert "hashed_password" not in data


def test_auth_login_workflow(client: TestClient) -> None:
    """Registered users can log in and receive a valid JWT token."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "LoginPass123!",
            "full_name": "Login Test User",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "LoginPass123!",
        },
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert token_data["email"] == "logintest@example.com"


def test_access_protected_endpoint_with_jwt(client: TestClient) -> None:
    """Accessing /users/me succeeds with a valid Bearer token."""
    # Register & login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "protected@example.com",
            "password": "ValidPass123!",
            "full_name": "Protected User",
        },
    )
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "protected@example.com",
            "password": "ValidPass123!",
        },
    )
    token = login_resp.json()["access_token"]

    me_resp = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "protected@example.com"


def test_reject_invalid_token_on_protected_endpoint(client: TestClient) -> None:
    """Protected endpoints reject invalid or malformed tokens with 401."""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer completely-invalid-junk-token"},
    )
    assert response.status_code == 401
