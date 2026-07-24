"""Configuration behavior tests."""

import pytest
from backend.app.core.config import Settings
from pydantic import ValidationError
from pytest import MonkeyPatch


def test_settings_accept_environment_overrides(monkeypatch: MonkeyPatch) -> None:
    """APP_* environment variables override safe defaults."""
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("APP_DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.log_level == "DEBUG"
    assert settings.debug is True


def test_non_development_environment_requires_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="APP_JWT_SECRET"):
        Settings(environment="production", jwt_secret=None, _env_file=None)


def test_production_rejects_weak_secrets_and_debug_mode() -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(environment="production", jwt_secret="too-short", _env_file=None)

    with pytest.raises(ValidationError, match="APP_DEBUG"):
        Settings(
            environment="production",
            jwt_secret="a-secure-production-secret-with-32-characters",
            debug=True,
            _env_file=None,
        )
