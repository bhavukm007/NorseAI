"""Shared pytest fixtures."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def test_settings(tmp_path) -> Settings:
    """Return isolated settings for tests."""
    return Settings(
        environment="test",
        docs_enabled=False,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        jwt_secret="test-secret",
        jwt_issuer="test-issuer",
        jwt_audience="test-audience",
    )


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    """Return a test client with application lifespan support."""
    with TestClient(create_app(test_settings)) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(test_settings: Settings):
    def build(
        role: str = "admin",
        overrides: dict | None = None,
        omitted: set[str] | None = None,
    ) -> dict[str, str]:
        now = datetime.now(UTC)
        claims = {
            "exp": now + timedelta(minutes=10),
            "iat": now,
            "nbf": now,
            "iss": test_settings.jwt_issuer,
            "aud": test_settings.jwt_audience,
            "sub": str(uuid.uuid4()),
            "username": f"{role}-user",
            "role": role,
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
