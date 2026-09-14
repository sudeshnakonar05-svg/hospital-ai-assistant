"""Integration tests for document upload, vector search, RAG chat, and emergencies."""

from fastapi.testclient import TestClient


def test_upload_rejects_bad_type(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Executable files are not accepted as knowledge documents."""
    response = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("malware.exe", b"not a document", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_upload_index_search_and_chat(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Staff can upload a policy, search it, and get a grounded chat answer with sources."""
    content = (
        "Mercy Harbor Hospital visiting hours are 10:00 AM to 8:00 PM daily "
        "for general wards. ICU visiting is limited to two visitors at a time "
        "between 11:00 AM and 1:00 PM and again between 5:00 PM and 7:00 PM."
    )
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("visiting_hours.md", content.encode("utf-8"), "text/markdown")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["status"] == "indexed"
    assert body["chunk_count"] >= 1

    search = client.post(
        "/api/v1/documents/search",
        headers=auth_headers,
        json={"query": "ICU visiting hours", "top_k": 3},
    )
    assert search.status_code == 200
    hits = search.json()
    assert hits
    assert hits[0]["filename"] == "visiting_hours.md"
    assert "score" in hits[0]

    chat = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "When can families visit the ICU?", "mode": "retrieval_only", "top_k": 3},
    )
    assert chat.status_code == 200
    payload = chat.json()
    assert payload["emergency"] is False
    assert payload["retrieved"] >= 1
    assert payload["sources"]
    assert "visiting_hours.md" in payload["answer"] or payload["sources"][0]["filename"] == "visiting_hours.md"
    assert "not a substitute" in payload["answer"].lower()

    sessions = client.get("/api/v1/chat/sessions", headers=auth_headers)
    assert sessions.status_code == 200
    assert sessions.json()


def test_emergency_chat_bypasses_retrieval(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Emergency language returns the safety message with no sources."""
    response = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "I have chest pain and cannot breathe"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["emergency"] is True
    assert payload["sources"] == []
    assert "911" in payload["answer"]


def test_deleted_document_is_not_retrieved_by_chat(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Deleting a document removes it from both the database and chatbot retrieval."""
    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("temporary_policy.txt", b"Temporary policy: visitor check-in is at the front desk.", "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    before_delete = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "Where is visitor check-in?", "mode": "retrieval_only"},
    )
    assert before_delete.status_code == 200
    assert any(source["document"] == "temporary_policy.txt" for source in before_delete.json()["sources"])

    deleted = client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert deleted.status_code == 204

    after_delete = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "Where is visitor check-in?", "mode": "retrieval_only"},
    )
    assert after_delete.status_code == 200
    assert not any(source["document"] == "temporary_policy.txt" for source in after_delete.json()["sources"])


def test_websocket_chat_status_events(client: TestClient, admin_token: str) -> None:
    """WebSocket clients receive ready, status, and answer events."""
    with client.websocket_connect(f"/api/v1/chat/ws?token={admin_token}") as websocket:
        ready = websocket.receive_json()
        assert ready["event"] == "ready"
        websocket.send_json({"message": "What are visiting hours?", "mode": "retrieval_only", "top_k": 2})
        events = [websocket.receive_json() for _ in range(3)]
        names = [event["event"] for event in events]
        assert "status" in names
        assert "answer" in names
