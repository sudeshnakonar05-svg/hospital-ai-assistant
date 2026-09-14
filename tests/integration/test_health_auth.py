"""Integration tests for health and authentication."""

from fastapi.testclient import TestClient


def test_health_is_public(client: TestClient) -> None:
    """Liveness does not require a JWT."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_checks_database(client: TestClient) -> None:
    """Readiness runs a database ping."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_protected_route_requires_jwt(client: TestClient) -> None:
    """Department list is unauthorized without a bearer token."""
    response = client.get("/api/v1/departments")
    assert response.status_code == 401


def test_register_login_and_me(client: TestClient) -> None:
    """Patients can register, receive a JWT, and read /users/me."""
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "patient@example.com",
            "password": "PatientPass123",
            "full_name": "Pat Patient",
        },
    )
    assert register.status_code == 201
    assert register.json()["role"] == "patient"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@example.com", "password": "PatientPass123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["token_type"] == "bearer"

    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "patient@example.com"


def test_duplicate_register_conflicts(client: TestClient) -> None:
    """The same email cannot register twice."""
    payload = {
        "email": "dup@example.com",
        "password": "PatientPass123",
        "full_name": "Dup User",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_invalid_login_is_rejected(client: TestClient) -> None:
    """Wrong passwords return 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPass123"},
    )
    assert response.status_code == 401


def test_validation_error_for_short_password(client: TestClient) -> None:
    """Pydantic rejects passwords under 8 characters."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "x@example.com", "password": "short", "full_name": "X Y"},
    )
    assert response.status_code == 422
