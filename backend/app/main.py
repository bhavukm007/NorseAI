"""FastAPI application factory and ASGI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.api.router import api_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging import configure_logging, get_logger
from backend.app.core.security import (
    RateLimiter,
    client_key,
    correlation_id_context,
    hash_password,
    request_id_context,
    valid_request_identifier,
)
from backend.app.db import Base, build_session_factory
from backend.app.errors import AppError
from backend.app.models import Role, User


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an independently configurable FastAPI application."""
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)
    logger = get_logger(__name__)
    session_factory = build_session_factory(resolved_settings.database_url)
    rate_limiter = RateLimiter()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if resolved_settings.environment == "test":
            Base.metadata.create_all(session_factory.kw["bind"])
        if resolved_settings.environment in {"development", "test"}:
            with session_factory() as session:
                operator = session.scalar(
                    select(User).where(User.username == resolved_settings.operator_username)
                )
                if operator is None:
                    session.add(
                        User(
                            username=resolved_settings.operator_username,
                            role=Role.ADMIN,
                            password_hash=hash_password(
                                resolved_settings.operator_password.get_secret_value()
                            ),
                        ),
                    )
                    session.commit()
                    logger.info(
                        "demo_administrator_created",
                        extra={"username": resolved_settings.operator_username},
                    )
                else:
                    if not operator.password_hash:
                        operator.password_hash = hash_password(
                            resolved_settings.operator_password.get_secret_value()
                        )
                        operator.enabled = True
                        session.commit()
                    logger.info(
                        "demo_administrator_detected",
                        extra={"username": resolved_settings.operator_username},
                    )
        logger.info(
            "application_started",
            extra={
                "app_name": resolved_settings.name,
                "environment": resolved_settings.environment,
            },
        )
        yield
        logger.info("application_stopped")

    application = FastAPI(
        title=resolved_settings.name,
        version=resolved_settings.version,
        debug=resolved_settings.debug,
        docs_url="/docs" if resolved_settings.docs_enabled else None,
        redoc_url="/redoc" if resolved_settings.docs_enabled else None,
        openapi_url=(
            f"{resolved_settings.api_v1_prefix}/openapi.json"
            if resolved_settings.docs_enabled
            else None
        ),
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.session_factory = session_factory

    @application.middleware("http")
    async def security_controls(request: Request, call_next):
        request_id = valid_request_identifier(request.headers.get("x-request-id"))
        correlation_id = valid_request_identifier(request.headers.get("x-correlation-id"))
        request_token = request_id_context.set(request_id)
        correlation_token = correlation_id_context.set(correlation_id)
        path = request.url.path
        limit = None
        if path.endswith("/auth/login"):
            limit = resolved_settings.login_rate_limit
        elif "/auth/" in path:
            limit = resolved_settings.auth_rate_limit
        elif path.endswith("/audit-logs/export"):
            limit = resolved_settings.audit_export_rate_limit
        elif path.endswith("/financial-actions") or "/financial-actions/" in path:
            limit = resolved_settings.financial_rate_limit
        if limit is not None:
            allowed, retry_after = rate_limiter.allow(
                f"{client_key(request)}:{path}",
                limit,
                resolved_settings.rate_limit_window_seconds,
            )
            if not allowed:
                response = JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": "Too many requests",
                        }
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        if path in {"/docs", "/redoc"}:
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src data: https://fastapi.tiangolo.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; base-uri 'none'"
            )
        else:
            response.headers["Content-Security-Policy"] = resolved_settings.csp_policy
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if resolved_settings.hsts_max_age and resolved_settings.environment in {
            "test",
            "staging",
            "production",
        }:
            response.headers["Strict-Transport-Security"] = (
                f"max-age={resolved_settings.hsts_max_age}; includeSubDomains"
            )
        request_id_context.reset(request_token)
        correlation_id_context.reset(correlation_token)
        return response

    @application.exception_handler(AppError)
    async def handle_app_error(_: Request, error: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == 401 else None
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
            headers=headers,
        )

    @application.exception_handler(IntegrityError)
    async def handle_integrity_error(_: Request, __: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "resource_conflict",
                    "message": "The request conflicts with an existing or referenced resource",
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed",
                },
                "details": jsonable_encoder(error.errors()),
            },
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in resolved_settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if resolved_settings.docs_enabled:

        @application.get("/openapi.json", include_in_schema=False)
        def root_openapi_schema():
            return application.openapi()

    application.include_router(api_router, prefix=resolved_settings.api_v1_prefix)
    return application


app = create_app()
