"""Integration tests for Department CRUD (Create, Read, Update, Delete)."""

from fastapi.testclient import TestClient


def test_department_crud_workflow(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Create, Read, Update, and Delete a department."""
    # 1. Create department
    create_resp = client.post(
        "/api/v1/departments",
        headers=auth_headers,
        json={
            "name": "Neurology",
            "description": "Brain and nervous system clinical care",
        },
    )
    assert create_resp.status_code == 201
    dept_id = create_resp.json()["id"]
    assert create_resp.json()["name"] == "Neurology"

    # 2. Read department
    read_resp = client.get(f"/api/v1/departments/{dept_id}", headers=auth_headers)
    assert read_resp.status_code == 200
    assert read_resp.json()["name"] == "Neurology"

    # Also list departments
    list_resp = client.get("/api/v1/departments", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(d["id"] == dept_id for d in list_resp.json())

    # 3. Update department (PUT / PATCH)
    update_resp = client.put(
        f"/api/v1/departments/{dept_id}",
        headers=auth_headers,
        json={
            "name": "Neurology and Neurosurgery",
            "description": "Advanced neuroscience and neurosurgery care",
        },
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Neurology and Neurosurgery"

    # 4. Delete department
    del_resp = client.delete(f"/api/v1/departments/{dept_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    # Verify deleted
    verify_resp = client.get(f"/api/v1/departments/{dept_id}", headers=auth_headers)
    assert verify_resp.status_code == 404
