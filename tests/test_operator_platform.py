"""Operator authentication and read-model API coverage."""


def test_operator_login_and_session(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "norseai-demo"},
    )
    assert response.status_code == 200
    session = response.json()
    assert session["token_type"] == "bearer"
    assert session["role"] == "admin"
    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {session['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_operator_login_rejects_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "incorrect"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


def test_operator_overview_and_audit_export(client, auth_headers):
    headers = auth_headers()
    client.post(
        "/api/v1/agents",
        headers=headers,
        json={"name": "Treasury Agent", "agent_type": "payments"},
    )
    overview = client.get("/api/v1/overview", headers=headers)
    csv_export = client.get("/api/v1/audit-logs/export?format=csv", headers=headers)
    jsonl_export = client.get("/api/v1/audit-logs/export?format=jsonl", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["active_agents"] == 1
    assert csv_export.status_code == 200
    assert csv_export.headers["content-type"].startswith("text/csv")
    assert "agent.create" in csv_export.text
    assert jsonl_export.status_code == 200
    assert jsonl_export.headers["content-type"].startswith("application/x-ndjson")
