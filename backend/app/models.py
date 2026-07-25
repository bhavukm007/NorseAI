"""Normalized Phase 2 persistence models."""

import enum
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from backend.app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class AgentStatus(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    SUSPENDED = "suspended"


class GovernanceStatus(str, enum.Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    EMERGENCY_STOPPED = "emergency_stopped"


class PolicyEffect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class LimitPeriod(str, enum.Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    TRANSACTION = "transaction"


class FinancialActionType(str, enum.Enum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    REFUND = "refund"


class FinancialActionStatus(str, enum.Enum):
    REJECTED = "rejected"
    SETTLED = "settled"
    REVERSED = "reversed"


class ReservationStatus(str, enum.Enum):
    RESERVED = "reserved"
    SETTLED = "settled"
    RELEASED = "released"
    REVERSED = "reversed"


class SpendRecordType(str, enum.Enum):
    SETTLEMENT = "settlement"
    REVERSAL = "reversal"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agents: Mapped[list["Agent"]] = relationship(back_populates="owner")
    sessions: Mapped[list["AuthSession"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        primaryjoin=lambda: User.id == foreign(AuditLog.user_id), viewonly=True
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    user: Mapped[User] = relationship(back_populates="sessions")


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    status: Mapped[GovernanceStatus] = mapped_column(
        Enum(GovernanceStatus, native_enum=False),
        default=GovernanceStatus.ENABLED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    fleets: Mapped[list["Fleet"]] = relationship(back_populates="organization")
    spend_limits: Mapped[list["OrganizationSpendLimit"]] = relationship(
        back_populates="organization", passive_deletes=True
    )


class Fleet(Base):
    __tablename__ = "fleets"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    status: Mapped[GovernanceStatus] = mapped_column(
        Enum(GovernanceStatus, native_enum=False),
        default=GovernanceStatus.ENABLED,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    organization: Mapped[Organization] = relationship(back_populates="fleets")
    agents: Mapped[list["Agent"]] = relationship(back_populates="fleet")
    spend_limits: Mapped[list["FleetSpendLimit"]] = relationship(
        back_populates="fleet", passive_deletes=True
    )


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    owner: Mapped[User | None] = relationship(back_populates="agents")
    fleet_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fleets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    fleet: Mapped[Fleet | None] = relationship(back_populates="agents")
    agent_type: Mapped[str] = mapped_column(String(100))
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, native_enum=False), default=AgentStatus.ENABLED, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="agent", passive_deletes=True
    )
    spend_limits: Mapped[list["SpendLimit"]] = relationship(
        back_populates="agent", passive_deletes=True
    )
    spend_records: Mapped[list["SpendRecord"]] = relationship(
        back_populates="agent", passive_deletes=True
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        primaryjoin=lambda: Agent.id == foreign(AuditLog.agent_id), viewonly=True
    )


class Policy(Base):
    __tablename__ = "policies"
    __table_args__ = (
        Index(
            "ix_policies_evaluation",
            "enabled",
            "action",
            "resource",
            "priority",
            "effect",
            "created_at",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    effect: Mapped[PolicyEffect] = mapped_column(Enum(PolicyEffect, native_enum=False))
    resource: Mapped[str] = mapped_column(String(200), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    conditions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    allows_uncapped_spend: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="policy", passive_deletes=True
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        primaryjoin=lambda: Policy.id == foreign(AuditLog.policy_id), viewonly=True
    )


class Permission(Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("agent_id", "policy_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agent: Mapped[Agent] = relationship(back_populates="permissions")
    policy: Mapped[Policy] = relationship(back_populates="permissions")


class SpendLimit(Base):
    __tablename__ = "spend_limits"
    __table_args__ = (UniqueConstraint("agent_id", "period", "currency"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[LimitPeriod] = mapped_column(Enum(LimitPeriod, native_enum=False))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    agent: Mapped[Agent] = relationship(back_populates="spend_limits")


class FleetSpendLimit(Base):
    __tablename__ = "fleet_spend_limits"
    __table_args__ = (UniqueConstraint("fleet_id", "period", "currency"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fleet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fleets.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[LimitPeriod] = mapped_column(Enum(LimitPeriod, native_enum=False))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    fleet: Mapped[Fleet] = relationship(back_populates="spend_limits")


class OrganizationSpendLimit(Base):
    __tablename__ = "organization_spend_limits"
    __table_args__ = (UniqueConstraint("organization_id", "period", "currency"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[LimitPeriod] = mapped_column(Enum(LimitPeriod, native_enum=False))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    organization: Mapped[Organization] = relationship(back_populates="spend_limits")


class SpendRecord(Base):
    __tablename__ = "spend_records"
    __table_args__ = (
        Index("ix_spend_records_agent_currency_timestamp", "agent_id", "currency", "timestamp"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    record_type: Mapped[SpendRecordType] = mapped_column(
        Enum(SpendRecordType, native_enum=False), default=SpendRecordType.SETTLEMENT
    )
    financial_action_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("financial_actions.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agent: Mapped[Agent] = relationship(back_populates="spend_records")


class FinancialAction(Base):
    __tablename__ = "financial_actions"
    __table_args__ = (
        UniqueConstraint("agent_id", "idempotency_key"),
        Index("ix_financial_actions_fleet_timestamp", "fleet_id", "timestamp"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4, unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    actor: Mapped[str] = mapped_column(String(100))
    agent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agents.id", ondelete="RESTRICT"), index=True
    )
    fleet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fleets.id", ondelete="RESTRICT"), index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    action_type: Mapped[FinancialActionType] = mapped_column(
        Enum(FinancialActionType, native_enum=False)
    )
    resource: Mapped[str] = mapped_column(String(200))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[FinancialActionStatus] = mapped_column(
        Enum(FinancialActionStatus, native_enum=False), index=True
    )
    permission_allowed: Mapped[bool] = mapped_column(Boolean)
    spend_allowed: Mapped[bool] = mapped_column(Boolean)
    policy_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    decision_reason: Mapped[str] = mapped_column(Text)
    adapter_reference: Mapped[str | None] = mapped_column(String(150), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class BudgetReservation(Base):
    __tablename__ = "budget_reservations"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    financial_action_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_actions.id", ondelete="CASCADE"), unique=True, index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(index=True)
    fleet_id: Mapped[uuid.UUID] = mapped_column(index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[ReservationStatus] = mapped_column(
        Enum(ReservationStatus, native_enum=False), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_agent_timestamp", "agent_reference", "timestamp"),
        Index("ix_audit_logs_user_timestamp", "username", "timestamp"),
        Index("ix_audit_logs_action_timestamp", "action", "timestamp"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True)
    user_reference: Mapped[uuid.UUID] = mapped_column(index=True)
    username: Mapped[str] = mapped_column(String(100))
    agent_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    agent_reference: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    resource: Mapped[str] = mapped_column(String(250))
    result: Mapped[str] = mapped_column(String(50))
    policy_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    policy_reference: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    fleet_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    policy_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    spend_decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    execution_result: Mapped[str | None] = mapped_column(String(50), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    decision_context: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    policy_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user: Mapped[User | None] = relationship(
        primaryjoin=lambda: foreign(AuditLog.user_id) == User.id, viewonly=True
    )
    agent: Mapped[Agent | None] = relationship(
        primaryjoin=lambda: foreign(AuditLog.agent_id) == Agent.id, viewonly=True
    )
    policy: Mapped[Policy | None] = relationship(
        primaryjoin=lambda: foreign(AuditLog.policy_id) == Policy.id, viewonly=True
    )


def _reject_audit_change(*_: Any, **__: Any) -> None:
    raise ValueError("Audit logs are immutable")


event.listen(AuditLog, "before_update", _reject_audit_change)
event.listen(AuditLog, "before_delete", _reject_audit_change)
event.listen(SpendRecord, "before_update", _reject_audit_change)
event.listen(SpendRecord, "before_delete", _reject_audit_change)
