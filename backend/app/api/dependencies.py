"""Shared FastAPI dependencies."""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.adapters.financial import SandboxFinancialAdapter
from backend.app.core.config import Settings
from backend.app.db import session_scope
from backend.app.errors import AppError
from backend.app.models import AuthSession, Role, User
from backend.app.repositories.governance import GovernanceRepositories
from backend.app.schemas.governance import Principal
from backend.app.services.agents import AgentService
from backend.app.services.base import AuditService
from backend.app.services.budgets import BudgetService
from backend.app.services.emergency import EmergencyService
from backend.app.services.financial_actions import FinancialActionService
from backend.app.services.fleets import FleetService
from backend.app.services.overview import OverviewService
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
    session: Annotated[Session, Depends(get_db)],
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
            options={
                "require": [
                    "exp",
                    "iat",
                    "nbf",
                    "iss",
                    "aud",
                    "sub",
                    "username",
                    "role",
                    "sid",
                    "ver",
                    "typ",
                ]
            },
        )
        if payload["typ"] != "access":
            raise ValueError("Unexpected token type")
        user_id = uuid.UUID(payload["sub"])
        session_id = uuid.UUID(payload["sid"])
        user = session.get(User, user_id)
        auth_session = session.get(AuthSession, session_id)
        session_expires_at = auth_session.expires_at if auth_session else None
        if session_expires_at and session_expires_at.tzinfo is None:
            session_expires_at = session_expires_at.replace(tzinfo=UTC)
        if (
            user is None
            or not user.enabled
            or user.username != payload["username"]
            or user.role != Role(payload["role"])
            or user.token_version != payload["ver"]
            or auth_session is None
            or auth_session.user_id != user.id
            or auth_session.revoked_at is not None
            or session_expires_at <= datetime.now(UTC)
        ):
            raise ValueError("User or session revoked")
        return Principal(
            id=user.id,
            username=user.username,
            role=user.role,
            session_id=session_id,
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
        self.fleets = FleetService(repositories, principal)
        self.budgets = BudgetService(repositories, principal)
        self.financial_actions = FinancialActionService(
            repositories, principal, SandboxFinancialAdapter()
        )
        self.overview = OverviewService(repositories, principal)


def get_services(
    session: Annotated[Session, Depends(get_db)],
    principal: Annotated[Principal, Depends(get_principal)],
) -> Services:
    return Services(GovernanceRepositories(session), principal)
