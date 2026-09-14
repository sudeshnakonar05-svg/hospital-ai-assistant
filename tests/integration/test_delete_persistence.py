"""Verify UI-facing delete endpoints remove records from the database."""

from pathlib import Path

from app.crud import appointment as appointment_crud
from app.crud import department as department_crud
from app.crud import doctor as doctor_crud
from app.crud import patient as patient_crud
from app.crud import knowledge_document as document_crud
from app.db.session import SessionLocal


def test_delete_endpoints_remove_database_records(client, auth_headers) -> None:
    """Delete every UI-managed resource and verify it is absent after commit."""
    department = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={"name": "Delete Test Department", "description": "Temporary"},
    ).json()
    doctor = client.post(
        "/api/v1/doctors",
        headers=auth_headers,
        json={
            "name": "Delete Test Doctor",
            "specialization": "Testing",
            "department_id": department["id"],
        },
    ).json()
    patient = client.post(
        "/api/v1/patients",
        headers=auth_headers,
        json={"name": "Delete Test Patient", "date_of_birth": "1990-01-01"},
    ).json()
    appointment = client.post(
        "/api/v1/appointments",
        headers=auth_headers,
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "appointment_date": "2026-12-01",
            "appointment_time": "12:00",
        },
    ).json()

    document = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("delete-test.md", b"temporary delete test", "text/markdown")},
    ).json()
    document_path = Path(document["file_path"])

    assert client.delete(f"/api/v1/appointments/{appointment['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/v1/documents/{document['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/v1/patients/{patient['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/v1/doctors/{doctor['id']}", headers=auth_headers).status_code == 204
    assert client.delete(f"/api/v1/departments/{department['id']}", headers=auth_headers).status_code == 204

    with SessionLocal() as db:
        assert appointment_crud.get_by_id(db, appointment["id"]) is None
        assert patient_crud.get_by_id(db, patient["id"]) is None
        assert doctor_crud.get_by_id(db, doctor["id"]) is None
        assert department_crud.get_by_id(db, department["id"]) is None
        assert document_crud.get_document(db, document["id"]) is None

    assert not document_path.exists()