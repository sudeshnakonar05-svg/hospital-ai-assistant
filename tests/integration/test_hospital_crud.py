"""Integration tests for department, doctor, patient, and appointment CRUD."""

from fastapi.testclient import TestClient


def test_patient_cannot_create_department(client: TestClient) -> None:
    """RBAC: patients are forbidden from staff-only writes."""
    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": "limited@example.com",
            "password": "PatientPass123",
            "full_name": "Limited User",
        },
    )
    assert register.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "limited@example.com", "password": "PatientPass123"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/departments",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Secret Ward", "description": "nope"},
    )
    assert response.status_code == 403


def test_full_appointment_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Admin can create a department, doctor, patient, and appointment."""
    department = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={
            "name": "Cardiology",
            "description": "Heart care",
            "extra": {"floor": 3},
        },
    )
    assert department.status_code == 201
    department_id = department.json()["id"]
    assert department.json()["extra"]["floor"] == 3

    listed = client.get("/api/v1/departments", headers=auth_headers)
    assert listed.status_code == 200
    assert any(item["name"] == "Cardiology" for item in listed.json())

    patched = client.patch(
        f"/api/v1/departments/{department_id}",
        headers=auth_headers,
        json={"description": "Heart and vascular care"},
    )
    assert patched.status_code == 200
    assert "vascular" in patched.json()["description"]

    doctor = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "department_id": department_id,
            "full_name": "Dr. Ada Heart",
            "specialization": "Interventional cardiology",
            "license_number": "MD-1001",
        },
    )
    assert doctor.status_code == 201
    doctor_id = doctor.json()["id"]

    missing_dept = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "department_id": 9999,
            "full_name": "Dr. Ghost",
            "specialization": "None",
            "license_number": "MD-404",
        },
    )
    assert missing_dept.status_code == 400

    patient = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "full_name": "Sam Sample",
            "date_of_birth": "1990-01-15",
            "medical_record_number": "MRN-500",
            "phone": "555-0100",
        },
    )
    assert patient.status_code == 201
    patient_id = patient.json()["id"]

    appointment = client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "scheduled_at": "2026-10-01T09:30:00Z",
            "reason": "Follow-up ECG",
        },
    )
    assert appointment.status_code == 201
    appointment_id = appointment.json()["id"]
    assert appointment.json()["status"] == "scheduled"

    updated = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        headers=auth_headers,
        json={"status": "completed"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"

    fetched = client.get(f"/api/v1/appointments/{appointment_id}", headers=auth_headers)
    assert fetched.status_code == 200

    delete_appt = client.delete(f"/api/v1/appointments/{appointment_id}", headers=auth_headers)
    assert delete_appt.status_code == 204
    assert client.get(f"/api/v1/appointments/{appointment_id}", headers=auth_headers).status_code == 404


def test_missing_department_is_not_found(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Unknown ids return 404."""
    response = client.get("/api/v1/departments/99999", headers=auth_headers)
    assert response.status_code == 404
