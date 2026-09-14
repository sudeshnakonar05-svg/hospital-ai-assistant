"""Integration tests for Doctor CRUD (Create doctor, Read doctor, Invalid department)."""

from fastapi.testclient import TestClient


def test_doctor_crud_and_validation(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Create doctor, read doctor, and reject invalid department ID."""
    # Create department first
    dept_resp = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={"name": "Pediatrics", "description": "Child healthcare"},
    )
    assert dept_resp.status_code == 201
    dept_id = dept_resp.json()["id"]

    # 1. Create doctor
    doc_payload = {
        "name": "Dr. Sarah Miller",
        "specialization": "Pediatrician",
        "department_id": dept_id,
        "phone": "+1-555-0199",
        "email": "sarah.miller@hospital.local",
    }
    doc_resp = client.post("/api/v1/doctors", headers=auth_headers, json=doc_payload)
    assert doc_resp.status_code == 201
    doc_data = doc_resp.json()
    assert doc_data["name"] == "Dr. Sarah Miller"
    doc_id = doc_data["id"]

    # 2. Read doctor
    read_resp = client.get(f"/api/v1/doctors/{doc_id}", headers=auth_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["name"] == "Dr. Sarah Miller"
    assert read_resp.json()["specialization"] == "Pediatrician"

    # Filter doctors by department
    filter_resp = client.get(f"/api/v1/doctors?department_id={dept_id}", headers=auth_headers)
    assert filter_resp.status_code == 200
    assert any(d["id"] == doc_id for d in filter_resp.json())

    # 3. Invalid department rejection
    invalid_resp = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "name": "Dr. Nonexistent Dept",
            "specialization": "Surgeon",
            "department_id": 999999,
            "phone": "+1-555-0000",
            "email": "invalid@hospital.local",
        },
    )
    assert invalid_resp.status_code == 400
