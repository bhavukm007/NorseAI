"""Version 1 route registry."""

from fastapi import APIRouter

from backend.app.api.v1.routes.auth import router as auth_router
from backend.app.api.v1.routes.governance import router as governance_router
from backend.app.api.v1.routes.health import router as health_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(governance_router)
