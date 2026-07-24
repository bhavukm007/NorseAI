"""Application errors independent of the transport layer."""


class AppError(Exception):
    """Stable application error surfaced by API exception handlers."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__("resource_not_found", f"{resource} not found", 404)
