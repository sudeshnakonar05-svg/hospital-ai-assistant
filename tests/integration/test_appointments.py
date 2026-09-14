"""Integration tests for Appointment CRUD (Create, Read, Invalid Doctor, Invalid Patient, Duplicate)."""

from fastapi.testclient import TestClient


def test_appointment_lifecycle_and_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Test creating, reading, validating missing entities, and detecting duplicate bookings."""
    # Setup department, doctor, patient
    dept = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={"name": "Orthopedics", "description": "Bone and joint health"},
    ).json()

    doctor = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "name": "Dr. Robert Bone",
            "specialization": "Orthopedic Surgeon",
            "department_id": dept["id"],
        },
    ).json()

    patient = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={
            "name": "Alice Patient",
            "date_of_birth": "1985-04-12",
        },
    ).json()

    # 1. Create appointment
    appt_payload = {
        "doctor_id": doctor["id"],
        "patient_id": patient["id"],
        "appointment_date": "2026-10-15",
        "appointment_time": "10:30",
        "reason": "Knee pain consultation",
    }
    create_resp = client.post("/api/v1/appointments", headers=auth_headers, json=appt_payload)
    assert create_resp.status_code == 201
    appt_data = create_resp.json()
    appt_id = appt_data["id"]
    assert appt_data["doctor_id"] == doctor["id"]
    assert appt_data["status"] == "scheduled"

    # 2. Read appointment
    read_resp = client.get(f"/api/v1/appointments/{appt_id}", headers=auth_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["id"] == appt_id
    assert read_resp.json()["reason"] == "Knee pain consultation"

    # 3. Invalid doctor rejection
    bad_doc_resp = client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "doctor_id": 999999,
            "patient_id": patient["id"],
            "appointment_date": "2026-10-15",
            "appointment_time": "11:00",
        },
    )
    assert bad_doc_resp.status_code == 400

    # 4. Invalid patient rejection
    bad_patient_resp = client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "doctor_id": doctor["id"],
            "patient_id": 999999,
            "appointment_date": "2026-10-15",
            "appointment_time": "11:00",
        },
    )
    assert bad_patient_resp.status_code == 400

    # 5. Duplicate appointment rejection (same doctor at same date and time)
    dup_resp = client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "appointment_date": "2026-10-15",
            "appointment_time": "10:30",
            "reason": "Duplicate booking attempt",
        },
    )
    assert dup_resp.status_code == 409
