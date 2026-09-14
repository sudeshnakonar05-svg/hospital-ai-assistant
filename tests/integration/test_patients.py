"""Integration tests for Patient CRUD (Create patient, Read patient, Update patient)."""

from fastapi.testclient import TestClient


def test_patient_crud_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Create, Read, and Update a patient profile."""
    # 1. Create patient
    payload = {
        "name": "Jane Doe",
        "date_of_birth": "1992-06-18",
        "gender": "Female",
        "phone": "+1-555-4321",
        "email": "jane.doe@example.com",
        "address": "123 Elm Street, Cityville",
    }
    create_resp = client.post("/api/v1/patients", headers=auth_headers, json=payload)
    assert create_resp.status_code == 201
    patient_data = create_resp.json()
    assert patient_data["name"] == "Jane Doe"
    assert patient_data["gender"] == "Female"
    patient_id = patient_data["id"]

    # 2. Read patient
    read_resp = client.get(f"/api/v1/patients/{patient_id}", headers=auth_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["name"] == "Jane Doe"
    assert read_resp.json()["email"] == "jane.doe@example.com"

    # 3. Update patient
    update_payload = {
        "phone": "+1-555-8888",
        "address": "456 Oak Avenue, Metropolis",
    }
    update_resp = client.put(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers,
        json=update_payload,
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["phone"] == "+1-555-8888"
    assert updated_data["address"] == "456 Oak Avenue, Metropolis"
    assert updated_data["name"] == "Jane Doe"
