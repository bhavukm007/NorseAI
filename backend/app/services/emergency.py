"""Emergency agent controls."""

import uuid

from backend.app.models import Agent, AgentStatus
from backend.app.services.base import Service


class EmergencyService(Service):
    def set_status(self, entity_id: uuid.UUID, value: AgentStatus) -> Agent:
        agent = self.repos.agents.get(entity_id)
        if not agent:
            raise self.not_found("Agent")
        agent.status = value
        self.repos.session.flush()
        self.audit.record(f"agent.{value.value}", f"agents/{agent.id}", agent_id=agent.id)
        return agent
