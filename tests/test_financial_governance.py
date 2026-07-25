"""Phase 06 governed financial-action integration tests."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from backend.app.models import AuditLog, FinancialAction, SpendRecord
from sqlalchemy import func, select


def build_governed_agent(client, headers, *, budget: str = "100.00"):
    organization = client.post(
        "/api/v1/organizations", json={"name": "Northstar Finance"}, headers=headers
    ).json()
    fleet = client.post(
        "/api/v1/fleets",
        json={"organization_id": organization["id"], "name": "Payments Fleet"},
        headers=headers,
    ).json()
    agent = client.post(
        "/api/v1/agents",
        json={
            "name": "treasury-agent",
            "agent_type": "financial",
            "fleet_id": fleet["id"],
        },
        headers=headers,
    ).json()
    policy = client.post(
        "/api/v1/policies",
        json={
            "name": "allow-payments",
            "effect": "allow",
            "resource": "accounts/operating",
            "action": "payment",
            "priority": 100,
        },
        headers=headers,
    ).json()
    client.post(
        "/api/v1/permissions",
        json={"agent_id": agent["id"], "policy_id": policy["id"]},
        headers=headers,
    )
    limit = {"period": "daily", "amount": budget, "currency": "USD"}
    client.post(
        "/api/v1/spend-limits",
        json={"agent_id": agent["id"], **limit},
        headers=headers,
    )
    client.post(
        f"/api/v1/fleets/{fleet['id']}/spend-limits",
        json=limit,
        headers=headers,
    )
    client.post(
        f"/api/v1/organizations/{organization['id']}/spend-limits",
        json=limit,
        headers=headers,
    )
    return organization, fleet, agent, policy


def execute(client, headers, agent_id, key, amount="25.00", action_type="payment"):
    return client.post(
        "/api/v1/financial-actions",
        json={
            "agent_id": agent_id,
            "idempotency_key": key,
            "action_type": action_type,
            "resource": "accounts/operating",
            "amount": amount,
            "currency": "USD",
        },
        headers=headers,
    )


def test_allowed_execution_settles_and_creates_complete_immutable_audit(
    client, auth_headers
) -> None:
    headers = auth_headers()
    _, fleet, agent, policy = build_governed_agent(client, headers)

    response = execute(client, headers, agent["id"], "allowed-1")

    assert response.status_code == 200
    result = response.json()
    assert result["allowed"] is True
    assert result["status"] == "settled"
    assert result["fleet_id"] == fleet["id"]
    assert result["policy_id"] == policy["id"]
    assert result["adapter_reference"].startswith("sandbox-payment-")
    with client.app.state.session_factory() as session:
        action = session.scalar(
            select(FinancialAction).where(FinancialAction.id == uuid.UUID(result["id"]))
        )
        audit = session.scalar(select(AuditLog).where(AuditLog.request_id == action.request_id))
        assert audit.username == "admin-user"
        assert audit.policy_decision == "allowed"
        assert audit.spend_decision == "allowed"
        assert audit.execution_result == "settled"
        assert audit.amount == Decimal("25.00")
        assert audit.currency == "USD"
        assert session.scalar(select(func.count()).select_from(SpendRecord)) == 1
        record = session.scalar(select(SpendRecord))
        record.amount = Decimal("1.00")
        with pytest.raises(ValueError, match="immutable"):
            session.flush()


def test_permission_denial_never_reaches_adapter(client, auth_headers) -> None:
    headers = auth_headers()
    _, _, agent, _ = build_governed_agent(client, headers)

    result = execute(client, headers, agent["id"], "denied-1", action_type="transfer").json()

    assert result["allowed"] is False
    assert result["permission_allowed"] is False
    assert result["spend_allowed"] is False
    assert result["adapter_reference"] is None


def test_insufficient_budget_rejects_without_execution(client, auth_headers) -> None:
    headers = auth_headers()
    _, _, agent, _ = build_governed_agent(client, headers)

    result = execute(client, headers, agent["id"], "over-budget", amount="101.00").json()

    assert result["allowed"] is False
    assert result["permission_allowed"] is True
    assert result["spend_allowed"] is False
    assert "budget exceeded" in result["reason"]
    assert result["adapter_reference"] is None


def test_disabled_agent_and_fleet_emergency_stop_block_execution(client, auth_headers) -> None:
    headers = auth_headers()
    _, fleet, agent, _ = build_governed_agent(client, headers)
    client.post(f"/api/v1/agents/{agent['id']}/disable", headers=headers)

    disabled = execute(client, headers, agent["id"], "disabled").json()

    assert disabled["allowed"] is False
    assert "Agent is disabled" in disabled["reason"]
    client.post(f"/api/v1/agents/{agent['id']}/enable", headers=headers)
    client.post(f"/api/v1/fleets/{fleet['id']}/emergency-stop", headers=headers)

    stopped = execute(client, headers, agent["id"], "fleet-stopped").json()

    assert stopped["allowed"] is False
    assert "Fleet is emergency_stopped" in stopped["reason"]
    assert stopped["adapter_reference"] is None


def test_idempotency_returns_original_execution_without_second_spend(client, auth_headers) -> None:
    headers = auth_headers()
    _, _, agent, _ = build_governed_agent(client, headers)

    first = execute(client, headers, agent["id"], "same-key").json()
    second = execute(client, headers, agent["id"], "same-key").json()

    assert second["id"] == first["id"]
    assert second["request_id"] == first["request_id"]
    assert second["idempotent_replay"] is True
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SpendRecord)) == 1


def test_cumulative_execution_cannot_exceed_shared_budget(client, auth_headers) -> None:
    headers = auth_headers()
    _, _, agent, _ = build_governed_agent(client, headers)

    def submit(key):
        return execute(client, headers, agent["id"], key, amount="60.00").json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, ("concurrent-a", "concurrent-b")))

    assert sorted(item["allowed"] for item in results) == [False, True]
    with client.app.state.session_factory() as session:
        assert session.scalar(select(func.count()).select_from(SpendRecord)) == 1


def test_explicit_uncapped_policy_allows_missing_budgets(client, auth_headers) -> None:
    headers = auth_headers()
    organization = client.post(
        "/api/v1/organizations", json={"name": "Uncapped Org"}, headers=headers
    ).json()
    fleet = client.post(
        "/api/v1/fleets",
        json={"organization_id": organization["id"], "name": "Uncapped Fleet"},
        headers=headers,
    ).json()
    agent = client.post(
        "/api/v1/agents",
        json={"name": "refund-agent", "agent_type": "financial", "fleet_id": fleet["id"]},
        headers=headers,
    ).json()
    policy = client.post(
        "/api/v1/policies",
        json={
            "name": "explicit-uncapped-refunds",
            "effect": "allow",
            "resource": "accounts/operating",
            "action": "refund",
            "allows_uncapped_spend": True,
        },
        headers=headers,
    ).json()
    client.post(
        "/api/v1/permissions",
        json={"agent_id": agent["id"], "policy_id": policy["id"]},
        headers=headers,
    )

    result = execute(client, headers, agent["id"], "uncapped-refund", action_type="refund").json()

    assert result["allowed"] is True
    assert result["status"] == "settled"


def test_reversal_appends_compensating_spend_record(client, auth_headers) -> None:
    headers = auth_headers()
    _, _, agent, _ = build_governed_agent(client, headers)
    settled = execute(client, headers, agent["id"], "reverse-me").json()

    reversed_action = client.post(
        f"/api/v1/financial-actions/{settled['id']}/reverse",
        json={"reason": "Sandbox operator reversal"},
        headers=headers,
    )

    assert reversed_action.status_code == 200
    assert reversed_action.json()["status"] == "reversed"
    with client.app.state.session_factory() as session:
        records = list(session.scalars(select(SpendRecord).order_by(SpendRecord.created_at)))
        assert [item.record_type.value for item in records] == ["settlement", "reversal"]
