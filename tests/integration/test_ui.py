"""Integration tests for web UI shell assets and root routing."""

from fastapi.testclient import TestClient


def test_root_endpoint_redirects_to_shell(client: TestClient) -> None:
    """Opening the root URL redirects to /ui/index.html."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/index.html"

    followed = client.get("/", follow_redirects=True)
    assert followed.status_code == 200
    assert "PulsePoint" in followed.text
    assert "AI Assistant" in followed.text
    assert "Appointments" in followed.text


def test_root_endpoint_metadata_json(client: TestClient) -> None:
    """API clients requesting JSON receive root metadata."""
    res_header = client.get("/", headers={"accept": "application/json"})
    assert res_header.status_code == 200
    data = res_header.json()
    assert data["status"] == "ok"
    assert "ui" in data

    res_param = client.get("/?format=json")
    assert res_param.status_code == 200
    assert res_param.json()["status"] == "ok"


def test_ui_index_html_shell_served(client: TestClient) -> None:
    """The static index shell is served at /ui/index.html with RBAC attributes."""
    response = client.get("/ui/index.html")
    assert response.status_code == 200
    assert "PulsePoint" in response.text
    assert "CareOS" in response.text
    assert "Appointments" in response.text
    assert 'data-roles="admin,staff"' in response.text
    assert "app.js" in response.text


def test_ui_static_assets_served(client: TestClient) -> None:
    """CSS and JavaScript files are served correctly with RBAC functions."""
    css_res = client.get("/ui/styles.css")
    assert css_res.status_code == 200
    assert "--primary" in css_res.text

    js_app = client.get("/ui/app.js")
    assert js_app.status_code == 200
    assert "sendChatQuery" in js_app.text
    assert "performLogin" in js_app.text
    assert "applyRolePermissions" in js_app.text
    assert "isAdminOrStaff" in js_app.text
