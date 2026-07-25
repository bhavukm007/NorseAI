"""Shared pytest fixtures."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.models import AuthSession, Role, User
from fastapi.testclient import TestClient
from sqlalchemy import select


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Return isolated settings for tests."""
    return Settings(
        environment="test",
        docs_enabled=False,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        jwt_secret="test-secret-that-is-at-least-32-bytes",
        jwt_issuer="test-issuer",
        jwt_audience="test-audience",
    )


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    """Return a test client with application lifespan support."""
    with TestClient(create_app(test_settings)) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(test_settings: Settings, client: TestClient):
    def build(
        role: str = "admin",
        overrides: dict | None = None,
        omitted: set[str] | None = None,
    ) -> dict[str, str]:
        now = datetime.now(UTC)
        username = f"{role}-user"
        with client.app.state.session_factory() as session:
            user = session.scalar(select(User).where(User.username == username))
            if user is None:
                user = User(
                    username=username,
                    role=Role(role),
                    password_hash="test-only",
                )
                session.add(user)
                session.flush()
            auth_session = AuthSession(
                user_id=user.id,
                refresh_token_hash=uuid.uuid4().hex + uuid.uuid4().hex,
                expires_at=now + timedelta(minutes=10),
            )
            session.add(auth_session)
            session.commit()
            user_id = user.id
            session_id = auth_session.id
            token_version = user.token_version
        claims = {
            "exp": now + timedelta(minutes=10),
            "iat": now,
            "nbf": now,
            "iss": test_settings.jwt_issuer,
            "aud": test_settings.jwt_audience,
            "sub": str(user_id),
            "username": username,
            "role": role,
            "sid": str(session_id),
            "ver": token_version,
            "typ": "access",
        }
        claims.update(overrides or {})
        for claim in omitted or set():
            claims.pop(claim, None)
        token = jwt.encode(
            claims,
            test_settings.jwt_secret.get_secret_value(),
            algorithm=test_settings.jwt_algorithm,
        )
        return {"Authorization": f"Bearer {token}"}

    return build
