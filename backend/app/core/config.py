"""Environment-backed application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated configuration loaded from APP_* environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore",
    )

    name: str = "NorseAI API"
    version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True
    cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [AnyHttpUrl("http://localhost:5173")]
    )
    database_url: str = "postgresql+psycopg://norseai:norseai@localhost:5432/norseai"
    jwt_secret: SecretStr | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "norseai"
    jwt_audience: str = "norseai-api"
    operator_username: str = "admin"
    operator_password: SecretStr = SecretStr("admin123")
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    refresh_token_days: int = Field(default=7, ge=1, le=90)
    login_rate_limit: int = Field(default=10, ge=1, le=1000)
    auth_rate_limit: int = Field(default=60, ge=1, le=10000)
    financial_rate_limit: int = Field(default=60, ge=1, le=10000)
    audit_export_rate_limit: int = Field(default=10, ge=1, le=1000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    hsts_max_age: int = Field(default=31536000, ge=0)
    csp_policy: str = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    redis_url: str = "redis://localhost:6379/0"
    opa_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8181")

    @model_validator(mode="after")
    def require_production_secret(self) -> "Settings":
        if self.environment != "development":
            if self.jwt_secret is None:
                raise ValueError("APP_JWT_SECRET is required outside development")
            if (
                self.environment in {"staging", "production"}
                and len(self.jwt_secret.get_secret_value()) < 32
            ):
                raise ValueError("APP_JWT_SECRET must contain at least 32 characters")
        if self.environment == "production" and self.debug:
            raise ValueError("APP_DEBUG must be false in production")
        if self.environment == "production" and self.operator_password.get_secret_value() in {
            "admin123",
            "norseai-demo",
        }:
            raise ValueError("APP_OPERATOR_PASSWORD must be changed in production")
        return self


@lru_cache
def get_settings() -> Settings:
    """Build settings once for dependency injection and application startup."""
    return Settings()
