"""Persistence-only repositories for governance entities."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session

from backend.app.db import Base
from backend.app.models import (
    Agent,
    AuditLog,
    Permission,
    Policy,
    PolicyEffect,
    SpendLimit,
    SpendRecord,
)

T = TypeVar("T", bound=Base)


class Repository(Generic[T]):
    def __init__(self, session: Session, model: type[T]) -> None:
        self.session = session
        self.model = model

    def get(self, entity_id: uuid.UUID) -> T | None:
        return self.session.get(self.model, entity_id)

    def list(self, offset: int, limit: int) -> list[T]:
        return list(
            self.session.scalars(
                select(self.model).order_by(self.model.id).offset(offset).limit(limit)
            )
        )

    def add(self, entity: T) -> T:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()


class GovernanceRepositories:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.agents = Repository(session, Agent)
        self.policies = Repository(session, Policy)
        self.permissions = Repository(session, Permission)
        self.spend_limits = Repository(session, SpendLimit)
        self.spend_records = Repository(session, SpendRecord)

    def matching_policies(self, agent_id: uuid.UUID, action: str, resource: str) -> list[Policy]:
        effect_order = case(
            (Policy.effect == PolicyEffect.DENY, 3),
            (Policy.effect == PolicyEffect.CONDITIONAL, 2),
            else_=1,
        )
        statement: Select[tuple[Policy]] = (
            select(Policy)
            .join(Permission, Permission.policy_id == Policy.id)
            .where(
                Permission.agent_id == agent_id,
                Policy.enabled.is_(True),
                Policy.action.in_((action, "*")),
                Policy.resource.in_((resource, "*")),
            )
            .order_by(
                Policy.priority.desc(),
                effect_order.desc(),
                Policy.created_at.asc(),
                Policy.id.asc(),
            )
        )
        return list(self.session.scalars(statement))

    def limits_for_agent(self, agent_id: uuid.UUID, currency: str) -> list[SpendLimit]:
        return list(
            self.session.scalars(
                select(SpendLimit)
                .where(
                    SpendLimit.agent_id == agent_id,
                    SpendLimit.currency == currency,
                )
                .with_for_update()
            )
        )

    def spent_between(
        self, agent_id: uuid.UUID, currency: str, start: datetime, end: datetime
    ) -> Decimal:
        amount = self.session.scalar(
            select(func.coalesce(func.sum(SpendRecord.amount), 0)).where(
                SpendRecord.agent_id == agent_id,
                SpendRecord.currency == currency,
                SpendRecord.timestamp >= start,
                SpendRecord.timestamp < end,
            )
        )
        return Decimal(amount)

    def audit(self, **values: Any) -> AuditLog:
        log = AuditLog(**values)
        self.session.add(log)
        self.session.flush()
        return log

    def list_audits(self, offset: int, limit: int) -> list[AuditLog]:
        statement = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        return list(self.session.scalars(statement))
