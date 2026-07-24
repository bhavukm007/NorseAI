"""Agent registry service."""

import uuid

from backend.app.models import Agent
from backend.app.schemas.governance import AgentCreate, AgentUpdate
from backend.app.services.base import Service


class AgentService(Service):
    def create(self, data: AgentCreate) -> Agent:
        agent = self.repos.agents.add(Agent(**data.model_dump()))
        self.audit.record("agent.create", f"agents/{agent.id}", agent_id=agent.id)
        return agent

    def get(self, entity_id: uuid.UUID) -> Agent:
        agent = self.repos.agents.get(entity_id)
        if not agent:
            raise self.not_found("Agent")
        return agent

    def list(self, offset: int, limit: int) -> list[Agent]:
        return self.repos.agents.list(offset, limit)

    def update(self, entity_id: uuid.UUID, data: AgentUpdate) -> Agent:
        agent = self.get(entity_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, key, value)
        self.repos.session.flush()
        self.audit.record("agent.update", f"agents/{agent.id}", agent_id=agent.id)
        return agent

    def delete(self, entity_id: uuid.UUID) -> None:
        agent = self.get(entity_id)
        self.audit.record("agent.delete", f"agents/{agent.id}", agent_id=agent.id)
        self.repos.agents.delete(agent)
