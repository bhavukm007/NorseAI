"""Phase 08 authentication, throttling, headers, and audit-integrity tests."""

from datetime import UTC, datetime, timedelta

from backend.app.models import AuditLog, AuthSession, User
from sqlalchemy import select

from tests.test_governance import create_agent


def test_login_refresh_rotation_logout_and_password_hash(client, test_settings) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_settings.operator_username,
            "password": test_settings.operator_password.get_secret_value(),
        },
    )
    assert login.status_code == 200
    first = login.json()
    assert first["refresh_token"] not in repr(client.app.state.session_factory.kw)
    with client.app.state.session_factory() as session:
        user = session.scalar(select(User).where(User.username == test_settings.operator_username))
        assert user.password_hash.startswith("scrypt$")
        assert test_settings.operator_password.get_secret_value() not in user.password_hash

    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert rotated.status_code == 200
    second = rotated.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        ).status_code
        == 401
    )
    headers = {"Authorization": f"Bearer {second['access_token']}"}
    assert client.post("/api/v1/auth/logout", json={}, headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_demo_administrator_bootstrap_is_idempotent(test_settings) -> None:
    from backend.app.main import create_app
    from fastapi.testclient import TestClient

    with (
        TestClient(create_app(test_settings)) as first,
        first.app.state.session_factory() as session,
    ):
        original = session.scalar(
            select(User).where(User.username == test_settings.operator_username)
        )
        original_hash = original.password_hash

    with (
        TestClient(create_app(test_settings)) as second,
        second.app.state.session_factory() as session,
    ):
        operators = list(
            session.scalars(select(User).where(User.username == test_settings.operator_username))
        )

    assert len(operators) == 1
    assert operators[0].password_hash == original_hash


def test_disabled_user_and_expired_session_are_rejected(client, auth_headers) -> None:
    headers = auth_headers()
    with client.app.state.session_factory() as session:
        user = session.scalar(select(User).where(User.username == "admin-user"))
        user.enabled = False
        session.commit()
    assert client.get("/api/v1/agents", headers=headers).status_code == 401

    headers = auth_headers("operator")
    with client.app.state.session_factory() as session:
        auth_session = session.scalar(select(AuthSession).order_by(AuthSession.created_at.desc()))
        auth_session.revoked_at = datetime.now(UTC) - timedelta(seconds=1)
        session.commit()
    assert client.get("/api/v1/agents", headers=headers).status_code == 401


def test_security_headers_and_rate_limit(tmp_path, test_settings) -> None:
    from backend.app.main import create_app
    from fastapi.testclient import TestClient

    settings = test_settings.model_copy(
        update={
            "database_url": f"sqlite:///{tmp_path / 'limited.db'}",
            "login_rate_limit": 1,
        }
    )
    with TestClient(create_app(settings)) as limited:
        response = limited.get("/api/v1/health")
        assert response.headers["content-security-policy"]
        assert response.headers["strict-transport-security"].startswith("max-age=")
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert response.headers["x-request-id"]
        credentials = {"username": "bad", "password": "bad"}
        assert limited.post("/api/v1/auth/login", json=credentials).status_code == 401
        throttled = limited.post("/api/v1/auth/login", json=credentials)
        assert throttled.status_code == 429
        assert throttled.headers["retry-after"]


def test_audit_contains_request_correlation_and_decision_context(client, auth_headers) -> None:
    headers = auth_headers()
    headers.update({"X-Request-ID": "audit-request", "X-Correlation-ID": "financial-workflow"})
    agent = create_agent(client, headers)
    client.post(
        "/api/v1/permissions/evaluate",
        json={
            "agent_id": agent["id"],
            "resource": "payments",
            "action": "submit",
            "context": {"region": "US"},
        },
        headers=headers,
    )
    with client.app.state.session_factory() as session:
        audit = session.scalar(
            select(AuditLog)
            .where(AuditLog.action == "permission.evaluate")
            .order_by(AuditLog.timestamp.desc())
        )
        assert audit.request_id is not None
        assert audit.correlation_id == "financial-workflow"
        assert audit.decision_context["context"] == {"region": "US"}
