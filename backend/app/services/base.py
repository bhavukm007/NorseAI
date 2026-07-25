"""Shared service primitives."""

import builtins
import copy
import uuid

from backend.app.core.security import correlation_id_context, request_id_context
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
        **details,
    ) -> AuditLog:
        request_id = details.pop("request_id", None)
        if request_id is None and request_id_context.get():
            try:
                request_id = uuid.UUID(request_id_context.get())
            except ValueError:
                request_id = uuid.uuid5(uuid.NAMESPACE_URL, request_id_context.get())
        metadata = copy.deepcopy(details.pop("metadata_json", {}))
        decision_context = copy.deepcopy(details.pop("decision_context", {}))
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
            request_id=request_id,
            correlation_id=correlation_id_context.get(),
            metadata_json=metadata,
            decision_context=decision_context,
            policy_version=details.pop("policy_version", None),
            **details,
        )

    def list(self, offset: int, limit: int) -> list[AuditLog]:
        return self.repos.list_audits(offset, limit)

    def filtered(self, **filters) -> builtins.list[AuditLog]:
        return self.repos.filtered_audits(**filters)
