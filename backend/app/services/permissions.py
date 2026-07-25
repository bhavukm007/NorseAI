"""Deterministic permission evaluation service."""

import uuid
from typing import Any

from backend.app.models import AgentStatus, Permission, PolicyEffect
from backend.app.schemas.governance import (
    EvaluationRequest,
    EvaluationResult,
    PermissionCreate,
)
from backend.app.services.base import Service


class PermissionService(Service):
    def assign(self, data: PermissionCreate) -> Permission:
        if not self.repos.agents.get(data.agent_id):
            raise self.not_found("Agent")
        if not self.repos.policies.get(data.policy_id):
            raise self.not_found("Policy")
        permission = self.repos.permissions.add(Permission(**data.model_dump()))
        self.audit.record(
            "permission.assign",
            f"permissions/{permission.id}",
            agent_id=data.agent_id,
            policy_id=data.policy_id,
        )
        return permission

    def list(self, offset: int, limit: int) -> list[Permission]:
        return self.repos.permissions.list(offset, limit)

    def unassign(self, permission_id: uuid.UUID) -> None:
        permission = self.repos.permissions.get(permission_id)
        if not permission:
            raise self.not_found("Permission")
        self.audit.record(
            "permission.unassign",
            f"permissions/{permission.id}",
            agent_id=permission.agent_id,
            policy_id=permission.policy_id,
        )
        self.repos.permissions.delete(permission)

    @staticmethod
    def _conditions_match(conditions: dict[str, Any], context: dict[str, Any]) -> bool:
        return all(context.get(key) == value for key, value in conditions.items())

    def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        agent = self.repos.agents.get(request.agent_id)
        if not agent:
            raise self.not_found("Agent")
        result = EvaluationResult(
            allowed=False, enforced_by_policy=None, reason="No applicable allow policy"
        )
        if agent.status != AgentStatus.ENABLED:
            result.reason = f"Agent is {agent.status.value}"
        else:
            for policy in self.repos.matching_policies(
                request.agent_id, request.action, request.resource
            ):
                if policy.effect == PolicyEffect.CONDITIONAL and not self._conditions_match(
                    policy.conditions, request.context
                ):
                    continue
                allowed = policy.effect in (PolicyEffect.ALLOW, PolicyEffect.CONDITIONAL)
                result = EvaluationResult(
                    allowed=allowed,
                    enforced_by_policy=policy.id,
                    reason=f"{policy.effect.value.title()} policy '{policy.name}' matched",
                )
                break
        self.audit.record(
            "permission.evaluate",
            request.resource,
            result="allowed" if result.allowed else "denied",
            agent_id=request.agent_id,
            policy_id=result.enforced_by_policy,
            decision_context=request.model_dump(mode="json"),
            policy_version=(
                str(self.repos.policies.get(result.enforced_by_policy).updated_at)
                if result.enforced_by_policy
                else None
            ),
        )
        return result
