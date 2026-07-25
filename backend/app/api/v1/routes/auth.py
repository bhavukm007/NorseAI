"""Persistent-user authentication with rotating, revocable sessions."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_db, get_principal, require_roles
from backend.app.core.security import hash_token, new_refresh_token, verify_password
from backend.app.errors import AppError
from backend.app.models import AuthSession, Role, User
from backend.app.schemas.governance import (
    LoginRequest,
    LogoutRequest,
    Principal,
    RefreshRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
Database = Annotated[Session, Depends(get_db)]
AdminPrincipal = Annotated[Principal, Depends(require_roles(Role.ADMIN))]


def _token_response(
    request: Request, user: User, auth_session: AuthSession, refresh_token: str
) -> TokenResponse:
    settings = request.app.state.settings
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_minutes)
    access_token = jwt.encode(
        {
            "exp": expires_at,
            "iat": now,
            "nbf": now,
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value,
            "sid": str(auth_session.id),
            "ver": user.token_version,
            "typ": "access",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        username=user.username,
        role=user.role,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, session: Database) -> TokenResponse:
    settings = request.app.state.settings
    if settings.jwt_secret is None:
        raise AppError("authentication_unavailable", "JWT authentication is not configured", 503)
    user = session.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise AppError("invalid_credentials", "Invalid username or password", 401)
    if not user.enabled:
        raise AppError("user_disabled", "User account is disabled", 403)
    refresh_token = new_refresh_token()
    auth_session = AuthSession(
        user_id=user.id,
        refresh_token_hash=hash_token(refresh_token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
    )
    session.add(auth_session)
    session.commit()
    session.refresh(auth_session)
    return _token_response(request, user, auth_session, refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, request: Request, session: Database) -> TokenResponse:
    now = datetime.now(UTC)
    auth_session = session.scalar(
        select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(data.refresh_token))
    )
    expires_at = auth_session.expires_at if auth_session else now
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if auth_session is None or auth_session.revoked_at is not None or expires_at <= now:
        raise AppError("invalid_refresh_token", "Refresh token is invalid or expired", 401)
    user = session.get(User, auth_session.user_id)
    if user is None or not user.enabled:
        auth_session.revoked_at = now
        session.commit()
        raise AppError("user_disabled", "User account is disabled or revoked", 401)
    rotated = new_refresh_token()
    auth_session.refresh_token_hash = hash_token(rotated)
    auth_session.last_rotated_at = now
    session.commit()
    return _token_response(request, user, auth_session, rotated)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    _: LogoutRequest,
    principal: Annotated[Principal, Depends(get_principal)],
    session: Database,
) -> Response:
    auth_session = session.get(AuthSession, principal.session_id)
    if auth_session is not None and auth_session.revoked_at is None:
        auth_session.revoked_at = datetime.now(UTC)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=Principal)
def me(principal: Annotated[Principal, Depends(get_principal)]) -> Principal:
    return principal


@router.post("/users/{user_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_user(user_id: str, _: AdminPrincipal, session: Database) -> Response:
    try:
        user = session.get(User, uuid.UUID(user_id))
    except ValueError as exc:
        raise AppError("user_not_found", "User not found", 404) from exc
    if user is None:
        raise AppError("user_not_found", "User not found", 404)
    user.enabled = False
    user.token_version += 1
    now = datetime.now(UTC)
    for auth_session in session.scalars(
        select(AuthSession).where(
            AuthSession.user_id == user.id,
            AuthSession.revoked_at.is_(None),
        )
    ):
        auth_session.revoked_at = now
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/users/{user_id}/enable", status_code=status.HTTP_204_NO_CONTENT)
def enable_user(user_id: str, _: AdminPrincipal, session: Database) -> Response:
    try:
        user = session.get(User, uuid.UUID(user_id))
    except ValueError as exc:
        raise AppError("user_not_found", "User not found", 404) from exc
    if user is None:
        raise AppError("user_not_found", "User not found", 404)
    user.enabled = True
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
