"""Shared service primitives."""

import uuid

from backend.app.errors import NotFoundError
from backend.app.models import AuditLog
from backend.app.repositories.governance import GovernanceRepositories
from backend.app.schemas.governance import Principal


class Service:
    def __init__(self, repositories: GovernanceRepositories, principal: Principal) -> None:
        self.repos = repositories
        self.principal = principal

    def not_found(self, resource: str) -> NotFoundError:
        return NotFoundError(resource)

    @property
    def audit(self) -> "AuditService":
        return AuditService(self.repos, self.principal)


class AuditService(Service):
    def record(
        self,
        action: str,
        resource: str,
        result: str = "success",
        agent_id: uuid.UUID | None = None,
        policy_id: uuid.UUID | None = None,
    ) -> AuditLog:
        return self.repos.audit(
            user_id=self.principal.id,
            user_reference=self.principal.id,
            username=self.principal.username,
            agent_id=agent_id,
            agent_reference=agent_id,
            action=action,
            resource=resource,
            result=result,
            policy_id=policy_id,
            policy_reference=policy_id,
        )

    def list(self, offset: int, limit: int) -> list[AuditLog]:
        return self.repos.list_audits(offset, limit)
