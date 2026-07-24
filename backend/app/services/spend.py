"""Spend-limit administration and transaction evaluation."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from backend.app.models import AgentStatus, LimitPeriod, SpendLimit, SpendRecord
from backend.app.schemas.governance import (
    SpendEvaluationRequest,
    SpendEvaluationResult,
    SpendLimitCreate,
    SpendLimitUpdate,
)
from backend.app.services.base import Service

PERIOD_ORDER = {
    LimitPeriod.TRANSACTION: 0,
    LimitPeriod.DAILY: 1,
    LimitPeriod.MONTHLY: 2,
}


class SpendService(Service):
    def create(self, data: SpendLimitCreate) -> SpendLimit:
        if not self.repos.agents.get(data.agent_id):
            raise self.not_found("Agent")
        limit = self.repos.spend_limits.add(SpendLimit(**data.model_dump()))
        self.audit.record("spend_limit.create", f"spend-limits/{limit.id}", agent_id=data.agent_id)
        return limit

    def get(self, entity_id: uuid.UUID) -> SpendLimit:
        limit = self.repos.spend_limits.get(entity_id)
        if not limit:
            raise self.not_found("Spend limit")
        return limit

    def list(self, offset: int, limit: int) -> list[SpendLimit]:
        return self.repos.spend_limits.list(offset, limit)

    def update(self, entity_id: uuid.UUID, data: SpendLimitUpdate) -> SpendLimit:
        limit = self.get(entity_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(limit, key, value)
        self.repos.session.flush()
        self.audit.record("spend_limit.update", f"spend-limits/{limit.id}", agent_id=limit.agent_id)
        return limit

    def delete(self, entity_id: uuid.UUID) -> None:
        limit = self.get(entity_id)
        self.audit.record("spend_limit.delete", f"spend-limits/{limit.id}", agent_id=limit.agent_id)
        self.repos.spend_limits.delete(limit)

    @staticmethod
    def _window(period: LimitPeriod, timestamp: datetime) -> tuple[datetime, datetime] | None:
        timestamp = timestamp.astimezone(UTC)
        if period == LimitPeriod.DAILY:
            start = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            return start, start + timedelta(days=1)
        if period == LimitPeriod.MONTHLY:
            start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (
                start.replace(year=start.year + 1, month=1)
                if start.month == 12
                else start.replace(month=start.month + 1)
            )
            return start, end
        return None

    def evaluate(self, data: SpendEvaluationRequest) -> SpendEvaluationResult:
        agent = self.repos.agents.get(data.agent_id)
        if not agent:
            raise self.not_found("Agent")
        if agent.status != AgentStatus.ENABLED:
            result = SpendEvaluationResult(
                allowed=False,
                reason=f"Agent is {agent.status.value}",
                violated_limit=None,
                remaining_limit=None,
            )
            self._audit_evaluation(data, result)
            return result

        limits = sorted(
            self.repos.limits_for_agent(data.agent_id, data.currency),
            key=lambda item: PERIOD_ORDER[item.period],
        )
        remaining_values: list[Decimal] = []
        for limit in limits:
            used = Decimal("0")
            window = self._window(limit.period, data.timestamp)
            if window:
                used = self.repos.spent_between(data.agent_id, data.currency, window[0], window[1])
            remaining = limit.amount - used
            if data.amount > remaining:
                result = SpendEvaluationResult(
                    allowed=False,
                    reason=f"{limit.period.value.title()} spend limit exceeded",
                    violated_limit=limit.period,
                    remaining_limit=max(remaining, Decimal("0")),
                )
                self._audit_evaluation(data, result)
                return result
            remaining_values.append(remaining - data.amount)

        self.repos.spend_records.add(
            SpendRecord(
                agent_id=data.agent_id,
                amount=data.amount,
                currency=data.currency,
                timestamp=data.timestamp,
            )
        )
        result = SpendEvaluationResult(
            allowed=True,
            reason="Transaction is within all configured spend limits",
            violated_limit=None,
            remaining_limit=min(remaining_values) if remaining_values else None,
        )
        self._audit_evaluation(data, result)
        return result

    def _audit_evaluation(
        self, data: SpendEvaluationRequest, result: SpendEvaluationResult
    ) -> None:
        self.audit.record(
            "spend.evaluate",
            f"spend/{data.currency}/{data.amount}",
            result="allowed" if result.allowed else "denied",
            agent_id=data.agent_id,
        )
