"""Phase 2 governance integration and unit tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient


def create_agent(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/agents",
        json={
            "name": "settlement-agent",
            "description": "Settles approved transactions",
            "agent_type": "payments",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_agent_crud_and_audit(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    updated = client.patch(
        f"/api/v1/agents/{agent['id']}",
        json={"description": "Updated"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Updated"
    assert client.get("/api/v1/agents", headers=headers).json()[0]["id"] == agent["id"]
    logs = client.get("/api/v1/audit-logs", headers=headers)
    assert logs.status_code == 200
    assert {item["action"] for item in logs.json()} >= {"agent.create", "agent.update"}
    assert client.delete(f"/api/v1/agents/{agent['id']}", headers=headers).status_code == 204


def test_policy_crud_permission_evaluation_and_kill_switch(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    policy_response = client.post(
        "/api/v1/policies",
        json={
            "name": "allow-low-risk",
            "effect": "conditional",
            "resource": "payments",
            "action": "submit",
            "conditions": {"risk": "low"},
            "priority": 10,
        },
        headers=headers,
    )
    assert policy_response.status_code == 201
    policy = policy_response.json()
    permission = client.post(
        "/api/v1/permissions",
        json={"agent_id": agent["id"], "policy_id": policy["id"]},
        headers=headers,
    )
    assert permission.status_code == 201
    allowed = client.post(
        "/api/v1/permissions/evaluate",
        json={
            "agent_id": agent["id"],
            "action": "submit",
            "resource": "payments",
            "context": {"risk": "low"},
        },
        headers=headers,
    )
    assert allowed.json()["allowed"] is True
    assert allowed.json()["enforced_by_policy"] == policy["id"]
    assert (
        client.post(f"/api/v1/agents/{agent['id']}/suspend", headers=headers).json()["status"]
        == "suspended"
    )
    denied = client.post(
        "/api/v1/permissions/evaluate",
        json={"agent_id": agent["id"], "action": "submit", "resource": "payments"},
        headers=headers,
    )
    assert denied.json()["allowed"] is False
    assert (
        client.post(f"/api/v1/agents/{agent['id']}/enable", headers=headers).json()["status"]
        == "enabled"
    )
    assert (
        client.patch(
            f"/api/v1/policies/{policy['id']}", json={"enabled": False}, headers=headers
        ).json()["enabled"]
        is False
    )
    assert client.delete(f"/api/v1/policies/{policy['id']}", headers=headers).status_code == 204


def test_spend_limit_crud(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    created = client.post(
        "/api/v1/spend-limits",
        json={
            "agent_id": agent["id"],
            "period": "daily",
            "amount": "1000.00",
            "currency": "USD",
        },
        headers=headers,
    )
    assert created.status_code == 201
    item = created.json()
    assert (
        client.patch(
            f"/api/v1/spend-limits/{item['id']}",
            json={"amount": "900.00"},
            headers=headers,
        ).json()["amount"]
        == "900.00"
    )
    assert len(client.get("/api/v1/spend-limits", headers=headers).json()) == 1
    assert client.delete(f"/api/v1/spend-limits/{item['id']}", headers=headers).status_code == 204


def test_spend_evaluation_applies_transaction_and_daily_limits(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    for period, amount in (("transaction", "60.00"), ("daily", "100.00"), ("monthly", "500.00")):
        response = client.post(
            "/api/v1/spend-limits",
            json={
                "agent_id": agent["id"],
                "period": period,
                "amount": amount,
                "currency": "USD",
            },
            headers=headers,
        )
        assert response.status_code == 201
    timestamp = datetime.now(UTC).isoformat()
    first = client.post(
        "/api/v1/spend/evaluate",
        json={
            "agent_id": agent["id"],
            "amount": "55.00",
            "currency": "USD",
            "timestamp": timestamp,
        },
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["allowed"] is True
    assert first.json()["remaining_limit"] == "5.00"
    transaction_denial = client.post(
        "/api/v1/spend/evaluate",
        json={
            "agent_id": agent["id"],
            "amount": "61.00",
            "currency": "USD",
            "timestamp": timestamp,
        },
        headers=headers,
    )
    assert transaction_denial.json()["violated_limit"] == "transaction"
    daily_denial = client.post(
        "/api/v1/spend/evaluate",
        json={
            "agent_id": agent["id"],
            "amount": "50.00",
            "currency": "USD",
            "timestamp": timestamp,
        },
        headers=headers,
    )
    assert daily_denial.json()["violated_limit"] == "daily"


def test_rbac_protects_writes_and_audit_data(client, auth_headers) -> None:
    assert client.get("/api/v1/agents").status_code == 401
    viewer = auth_headers("viewer")
    assert (
        client.post(
            "/api/v1/agents",
            json={"name": "x", "agent_type": "test"},
            headers=viewer,
        ).status_code
        == 403
    )
    assert client.get("/api/v1/audit-logs", headers=viewer).status_code == 403
    auditor = auth_headers("auditor")
    assert client.get("/api/v1/audit-logs", headers=auditor).status_code == 200
