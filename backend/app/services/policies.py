"""Policy administration service."""

import uuid

from backend.app.models import Policy
from backend.app.schemas.governance import PolicyCreate, PolicyUpdate
from backend.app.services.base import Service


class PolicyService(Service):
    def create(self, data: PolicyCreate) -> Policy:
        policy = self.repos.policies.add(Policy(**data.model_dump()))
        self.audit.record("policy.create", f"policies/{policy.id}", policy_id=policy.id)
        return policy

    def get(self, entity_id: uuid.UUID) -> Policy:
        policy = self.repos.policies.get(entity_id)
        if not policy:
            raise self.not_found("Policy")
        return policy

    def list(self, offset: int, limit: int) -> list[Policy]:
        return self.repos.policies.list(offset, limit)

    def update(self, entity_id: uuid.UUID, data: PolicyUpdate) -> Policy:
        policy = self.get(entity_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(policy, key, value)
        self.repos.session.flush()
        self.audit.record("policy.update", f"policies/{policy.id}", policy_id=policy.id)
        return policy

    def delete(self, entity_id: uuid.UUID) -> None:
        policy = self.get(entity_id)
        self.audit.record("policy.delete", f"policies/{policy.id}", policy_id=policy.id)
        self.repos.policies.delete(policy)
