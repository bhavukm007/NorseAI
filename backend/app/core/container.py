"""Dependency injection container foundation."""

from dataclasses import dataclass

from backend.app.core.config import Settings


@dataclass(frozen=True, slots=True)
class ApplicationContainer:
    """Explicit dependency registry for future services and repositories."""

    settings: Settings
