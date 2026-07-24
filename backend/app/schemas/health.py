"""Health endpoint schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Public API health representation."""

    model_config = ConfigDict(frozen=True)

    status: Literal["healthy"]
    service: str
    version: str
    environment: str
