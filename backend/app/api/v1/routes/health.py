"""Service health endpoint."""

from fastapi import APIRouter, status

from backend.app.api.dependencies import SettingsDependency
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get API health",
)
async def get_health(settings: SettingsDependency) -> HealthResponse:
    """Return lightweight liveness information without external dependencies."""
    return HealthResponse(
        status="healthy",
        service=settings.name,
        version=settings.version,
        environment=settings.environment,
    )
