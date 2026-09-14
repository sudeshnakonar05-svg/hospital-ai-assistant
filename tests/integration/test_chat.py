"""Integration tests for RAG Chat (Relevant Knowledge, No Relevant Knowledge, Emergency)."""

from fastapi.testclient import TestClient


def test_chat_with_relevant_knowledge(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Upload policy document, index it into FAISS, and verify grounded answer with sources."""
    content = (
        "St. Jude Memorial Hospital general ward visiting hours are 10:00 AM to 8:00 PM daily. "
        "ICU visiting hours are 11:00 AM to 12:00 PM and 5:00 PM to 6:30 PM. "
        "A maximum of two visitors per patient is allowed at any time."
    )
    # 1. Upload & index document
    upload_resp = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("visiting_policy.txt", content.encode("utf-8"), "text/plain")},
    )
    assert upload_resp.status_code == 201

    # 2. Ask question with relevant knowledge
    chat_resp = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "What are the visiting hours for the ICU?", "mode": "retrieval_only"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["emergency"] is False
    assert len(data["sources"]) >= 1
    assert "visiting_policy.txt" in data["sources"][0]["document"] or data["sources"][0]["filename"] == "visiting_policy.txt"
    assert "11:00 AM" in data["answer"] or "visiting_policy.txt" in data["answer"]


def test_chat_with_no_relevant_knowledge(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Unrelated questions should not invent answers and clearly state lack of information."""
    chat_resp = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "Who won the 1994 FIFA World Cup soccer tournament?", "mode": "retrieval_only"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["emergency"] is False
    # Should explain that the information is not available in the hospital knowledge base
    assert "could not find this information" in data["answer"].lower() or "not available" in data["answer"].lower() or not data["sources"]


def test_chat_emergency_question(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Emergency-style question bypasses RAG and returns safety response immediately."""
    chat_resp = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "I am having severe chest pain. What should I do?"},
    )
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert data["emergency"] is True
    assert data["sources"] == []
    assert "emergency" in data["answer"].lower()
