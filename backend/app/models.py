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


class PolicyEffect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class LimitPeriod(str, enum.Enum):
    DAILY = "daily"
    MONTHLY = "monthly"
    TRANSACTION = "transaction"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agents: Mapped[list["Agent"]] = relationship(back_populates="owner")
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        primaryjoin=lambda: User.id == foreign(AuditLog.user_id), viewonly=True
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
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    agent: Mapped[Agent] = relationship(back_populates="spend_records")


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
