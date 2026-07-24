"""Production-hardening behavior tests."""

from datetime import UTC, datetime, timedelta

import pytest
from backend.app.models import AuditLog, Permission
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from tests.test_governance import create_agent


def create_policy(
    client: TestClient,
    headers: dict[str, str],
    name: str,
    effect: str,
    priority: int,
    *,
    enabled: bool = True,
    conditions: dict | None = None,
) -> dict:
    response = client.post(
        "/api/v1/policies",
        json={
            "name": name,
            "effect": effect,
            "resource": "payments",
            "action": "submit",
            "priority": priority,
            "enabled": enabled,
            "conditions": conditions or {},
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def assign(client: TestClient, headers: dict[str, str], agent_id: str, policy_id: str) -> None:
    response = client.post(
        "/api/v1/permissions",
        json={"agent_id": agent_id, "policy_id": policy_id},
        headers=headers,
    )
    assert response.status_code == 201


def evaluate(client: TestClient, headers: dict[str, str], agent_id: str, context=None) -> dict:
    return client.post(
        "/api/v1/permissions/evaluate",
        json={
            "agent_id": agent_id,
            "resource": "payments",
            "action": "submit",
            "context": context or {},
        },
        headers=headers,
    ).json()


def test_equal_priority_uses_deny_effect_precedence(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    allow = create_policy(client, headers, "equal-allow", "allow", 10)
    deny = create_policy(client, headers, "equal-deny", "deny", 10)
    assign(client, headers, agent["id"], allow["id"])
    assign(client, headers, agent["id"], deny["id"])
    result = evaluate(client, headers, agent["id"])
    assert result["allowed"] is False
    assert result["enforced_by_policy"] == deny["id"]


def test_higher_priority_wins_and_disabled_policy_is_ignored(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    deny = create_policy(client, headers, "low-deny", "deny", 5)
    allow = create_policy(client, headers, "high-allow", "allow", 10)
    disabled = create_policy(client, headers, "disabled-deny", "deny", 20, enabled=False)
    for policy in (deny, allow, disabled):
        assign(client, headers, agent["id"], policy["id"])
    result = evaluate(client, headers, agent["id"])
    assert result["allowed"] is True
    assert result["enforced_by_policy"] == allow["id"]


def test_conditional_policy_requires_matching_context(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    policy = create_policy(
        client,
        headers,
        "conditional",
        "conditional",
        10,
        conditions={"region": "US"},
    )
    assign(client, headers, agent["id"], policy["id"])
    assert evaluate(client, headers, agent["id"], {"region": "EU"})["allowed"] is False
    assert evaluate(client, headers, agent["id"], {"region": "US"})["allowed"] is True


@pytest.mark.parametrize(
    ("overrides", "omitted"),
    [
        ({"exp": datetime.now(UTC) - timedelta(seconds=1)}, None),
        ({"iss": "wrong-issuer"}, None),
        ({"aud": "wrong-audience"}, None),
        (None, {"exp"}),
        (None, {"sub"}),
    ],
)
def test_invalid_jwt_claims_are_rejected(client, auth_headers, overrides, omitted) -> None:
    response = client.get(
        "/api/v1/agents",
        headers=auth_headers(overrides=overrides, omitted=omitted),
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "invalid_token"


@pytest.mark.parametrize(
    ("role", "read_status", "write_status", "delete_status", "audit_status"),
    [
        ("admin", 200, 201, 204, 200),
        ("operator", 200, 201, 403, 403),
        ("auditor", 200, 403, 403, 200),
        ("viewer", 200, 403, 403, 403),
    ],
)
def test_rbac_matrix(
    client,
    auth_headers,
    role,
    read_status,
    write_status,
    delete_status,
    audit_status,
) -> None:
    admin = auth_headers()
    agent = create_agent(client, admin)
    headers = auth_headers(role)
    assert client.get("/api/v1/agents", headers=headers).status_code == read_status
    assert (
        client.post(
            "/api/v1/agents",
            json={"name": f"{role}-agent", "agent_type": "test"},
            headers=headers,
        ).status_code
        == write_status
    )
    assert (
        client.delete(f"/api/v1/agents/{agent['id']}", headers=headers).status_code == delete_status
    )
    assert client.get("/api/v1/audit-logs", headers=headers).status_code == audit_status


def test_delete_cascades_permission_and_preserves_audit_reference(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    policy = create_policy(client, headers, "cascade-policy", "allow", 1)
    assign(client, headers, agent["id"], policy["id"])
    assert client.delete(f"/api/v1/agents/{agent['id']}", headers=headers).status_code == 204
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(Permission)) == 0
        audit = session.scalar(
            select(AuditLog)
            .where(AuditLog.action == "agent.delete")
            .order_by(AuditLog.timestamp.desc())
        )
        assert str(audit.agent_reference) == agent["id"]
        audit.result = "tampered"
        with pytest.raises(ValueError, match="immutable"):
            session.flush()


def test_duplicate_assignment_rolls_back_its_audit(client, auth_headers) -> None:
    headers = auth_headers()
    agent = create_agent(client, headers)
    policy = create_policy(client, headers, "rollback-policy", "allow", 1)
    assign(client, headers, agent["id"], policy["id"])
    before = len(client.get("/api/v1/audit-logs", headers=headers).json())
    duplicate = client.post(
        "/api/v1/permissions",
        json={"agent_id": agent["id"], "policy_id": policy["id"]},
        headers=headers,
    )
    assert duplicate.status_code == 409
    after = len(client.get("/api/v1/audit-logs", headers=headers).json())
    assert after == before
