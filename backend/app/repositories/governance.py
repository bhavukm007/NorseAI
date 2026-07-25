"""Persistence-only repositories for governance entities."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session

from backend.app.db import Base
from backend.app.models import (
    Agent,
    AuditLog,
    BudgetReservation,
    FinancialAction,
    Fleet,
    FleetSpendLimit,
    Organization,
    OrganizationSpendLimit,
    Permission,
    Policy,
    PolicyEffect,
    ReservationStatus,
    SpendLimit,
    SpendRecord,
    SpendRecordType,
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
        self.organizations = Repository(session, Organization)
        self.fleets = Repository(session, Fleet)
        self.policies = Repository(session, Policy)
        self.permissions = Repository(session, Permission)
        self.spend_limits = Repository(session, SpendLimit)
        self.fleet_spend_limits = Repository(session, FleetSpendLimit)
        self.organization_spend_limits = Repository(session, OrganizationSpendLimit)
        self.spend_records = Repository(session, SpendRecord)
        self.financial_actions = Repository(session, FinancialAction)
        self.budget_reservations = Repository(session, BudgetReservation)

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

    def limits_for_fleet(self, fleet_id: uuid.UUID, currency: str) -> list[FleetSpendLimit]:
        return list(
            self.session.scalars(
                select(FleetSpendLimit)
                .where(
                    FleetSpendLimit.fleet_id == fleet_id,
                    FleetSpendLimit.currency == currency,
                )
                .with_for_update()
            )
        )

    def limits_for_organization(
        self, organization_id: uuid.UUID, currency: str
    ) -> list[OrganizationSpendLimit]:
        return list(
            self.session.scalars(
                select(OrganizationSpendLimit)
                .where(
                    OrganizationSpendLimit.organization_id == organization_id,
                    OrganizationSpendLimit.currency == currency,
                )
                .with_for_update()
            )
        )

    def spent_between(
        self, agent_id: uuid.UUID, currency: str, start: datetime, end: datetime
    ) -> Decimal:
        amount = self.session.scalar(
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                SpendRecord.record_type == SpendRecordType.REVERSAL,
                                -SpendRecord.amount,
                            ),
                            else_=SpendRecord.amount,
                        )
                    ),
                    0,
                )
            ).where(
                SpendRecord.agent_id == agent_id,
                SpendRecord.currency == currency,
                SpendRecord.timestamp >= start,
                SpendRecord.timestamp < end,
            )
        )
        return Decimal(amount)

    def scoped_spent_between(
        self,
        scope: str,
        scope_id: uuid.UUID,
        currency: str,
        start: datetime,
        end: datetime,
    ) -> Decimal:
        statement = (
            select(
                func.coalesce(
                    func.sum(
                        case(
                            (
                                SpendRecord.record_type == SpendRecordType.REVERSAL,
                                -SpendRecord.amount,
                            ),
                            else_=SpendRecord.amount,
                        )
                    ),
                    0,
                )
            )
            .join(FinancialAction, SpendRecord.financial_action_id == FinancialAction.id)
            .where(
                getattr(FinancialAction, f"{scope}_id") == scope_id,
                SpendRecord.currency == currency,
                SpendRecord.timestamp >= start,
                SpendRecord.timestamp < end,
            )
        )
        return Decimal(self.session.scalar(statement))

    def active_reserved(self, scope: str, scope_id: uuid.UUID, currency: str) -> Decimal:
        amount = self.session.scalar(
            select(func.coalesce(func.sum(BudgetReservation.amount), 0)).where(
                getattr(BudgetReservation, f"{scope}_id") == scope_id,
                BudgetReservation.currency == currency,
                BudgetReservation.status == ReservationStatus.RESERVED,
            )
        )
        return Decimal(amount)

    def financial_action_by_idempotency(
        self, agent_id: uuid.UUID, idempotency_key: str
    ) -> FinancialAction | None:
        return self.session.scalar(
            select(FinancialAction).where(
                FinancialAction.agent_id == agent_id,
                FinancialAction.idempotency_key == idempotency_key,
            )
        )

    def audit(self, **values: Any) -> AuditLog:
        log = AuditLog(**values)
        self.session.add(log)
        self.session.flush()
        return log

    def list_audits(self, offset: int, limit: int) -> list[AuditLog]:
        statement = select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        return list(self.session.scalars(statement))

    def filtered_audits(
        self,
        *,
        offset: int,
        limit: int,
        search: str | None = None,
        actor: str | None = None,
        fleet_id: uuid.UUID | None = None,
        organization_id: uuid.UUID | None = None,
        policy_id: uuid.UUID | None = None,
        action: str | None = None,
        result: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[AuditLog]:
        statement = select(AuditLog)
        if search:
            value = f"%{search}%"
            statement = statement.where(
                or_(
                    AuditLog.username.ilike(value),
                    AuditLog.action.ilike(value),
                    AuditLog.resource.ilike(value),
                    AuditLog.result.ilike(value),
                )
            )
        if actor:
            statement = statement.where(AuditLog.username == actor)
        if fleet_id:
            statement = statement.where(AuditLog.fleet_id == fleet_id)
        if organization_id:
            statement = statement.where(AuditLog.organization_id == organization_id)
        if policy_id:
            statement = statement.where(AuditLog.policy_reference == policy_id)
        if action:
            statement = statement.where(AuditLog.action == action)
        if result:
            statement = statement.where(AuditLog.result == result)
        if date_from:
            statement = statement.where(AuditLog.timestamp >= date_from)
        if date_to:
            statement = statement.where(AuditLog.timestamp <= date_to)
        return list(
            self.session.scalars(
                statement.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
            )
        )
