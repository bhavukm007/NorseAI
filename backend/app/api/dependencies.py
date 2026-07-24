"""Shared FastAPI dependencies."""

import uuid
from collections.abc import Iterator
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.db import session_scope
from backend.app.errors import AppError
from backend.app.models import Role
from backend.app.repositories.governance import GovernanceRepositories
from backend.app.schemas.governance import Principal
from backend.app.services.agents import AgentService
from backend.app.services.base import AuditService
from backend.app.services.emergency import EmergencyService
from backend.app.services.permissions import PermissionService
from backend.app.services.policies import PolicyService
from backend.app.services.spend import SpendService


def get_request_settings(request: Request) -> Settings:
    """Return settings owned by the current application instance."""
    return request.app.state.settings


SettingsDependency = Annotated[Settings, Depends(get_request_settings)]

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    yield from session_scope(request.app.state.session_factory)


def get_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Principal:
    if not credentials:
        raise AppError("authentication_required", "Bearer token required", 401)
    try:
        settings = request.app.state.settings
        if settings.jwt_secret is None:
            raise AppError(
                "authentication_unavailable", "JWT authentication is not configured", 503
            )
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["exp", "iat", "nbf", "iss", "aud", "sub", "username", "role"]},
        )
        return Principal(
            id=uuid.UUID(payload["sub"]) if payload.get("sub") else None,
            username=payload["username"],
            role=Role(payload["role"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise AppError("invalid_token", "Invalid or expired bearer token", 401) from exc


def require_roles(*roles: Role):
    def dependency(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
        if principal.role not in roles:
            raise AppError("insufficient_role", "Insufficient role", 403)
        return principal

    return dependency


class Services:
    def __init__(self, repositories: GovernanceRepositories, principal: Principal) -> None:
        self.agents = AgentService(repositories, principal)
        self.policies = PolicyService(repositories, principal)
        self.permissions = PermissionService(repositories, principal)
        self.spend = SpendService(repositories, principal)
        self.audit = AuditService(repositories, principal)
        self.emergency = EmergencyService(repositories, principal)


def get_services(
    session: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(get_principal)],
) -> Services:
    return Services(GovernanceRepositories(session), principal)
