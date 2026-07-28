"""Validated Phase 2 API contracts."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models import (
    AgentStatus,
    FinancialActionStatus,
    FinancialActionType,
    GovernanceStatus,
    LimitPeriod,
    PolicyEffect,
    Role,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Principal(BaseModel):
    id: uuid.UUID | None = None
    username: str
    role: Role
    session_id: uuid.UUID | None = None


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=2000)
    owner_id: uuid.UUID | None = None
    fleet_id: uuid.UUID | None = None
    agent_type: str = Field(min_length=1, max_length=100)

    @field_validator("name", "agent_type")
    @classmethod
    def no_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


class AgentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    owner_id: uuid.UUID | None = None
    fleet_id: uuid.UUID | None = None
    agent_type: str | None = Field(default=None, min_length=1, max_length=100)


class AgentRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    owner_id: uuid.UUID | None
    fleet_id: uuid.UUID | None
    agent_type: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    effect: PolicyEffect
    resource: str = Field(min_length=1, max_length=200)
    action: str = Field(min_length=1, max_length=100)
    conditions: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0, le=1_000_000)
    enabled: bool = True
    allows_uncapped_spend: bool = False


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    effect: PolicyEffect | None = None
    resource: str | None = Field(default=None, min_length=1, max_length=200)
    action: str | None = Field(default=None, min_length=1, max_length=100)
    conditions: dict[str, Any] | None = None
    priority: int | None = Field(default=None, ge=0, le=1_000_000)
    enabled: bool | None = None
    allows_uncapped_spend: bool | None = None


class PolicyRead(ORMModel):
    id: uuid.UUID
    name: str
    effect: PolicyEffect
    resource: str
    action: str
    conditions: dict[str, Any]
    priority: int
    enabled: bool
    allows_uncapped_spend: bool
    created_at: datetime
    updated_at: datetime


class PermissionCreate(BaseModel):
    agent_id: uuid.UUID
    policy_id: uuid.UUID


class PermissionRead(ORMModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    policy_id: uuid.UUID
    created_at: datetime


class EvaluationRequest(BaseModel):
    agent_id: uuid.UUID
    action: str = Field(min_length=1, max_length=100)
    resource: str = Field(min_length=1, max_length=200)
    context: dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    allowed: bool
    enforced_by_policy: uuid.UUID | None
    reason: str


class SpendEvaluationRequest(BaseModel):
    agent_id: uuid.UUID
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value


class SpendEvaluationResult(BaseModel):
    allowed: bool
    reason: str
    violated_limit: LimitPeriod | None
    remaining_limit: Decimal | None


class SpendLimitCreate(BaseModel):
    agent_id: uuid.UUID
    period: LimitPeriod
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class SpendLimitUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=18, decimal_places=2)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")


class SpendLimitRead(ORMModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    period: LimitPeriod
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class OrganizationUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class OrganizationRead(ORMModel):
    id: uuid.UUID
    name: str
    status: GovernanceStatus
    created_at: datetime
    updated_at: datetime


class FleetCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)


class FleetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    organization_id: uuid.UUID | None = None


class FleetRead(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    status: GovernanceStatus
    created_at: datetime
    updated_at: datetime


class ScopedSpendLimitCreate(BaseModel):
    period: LimitPeriod
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")


class FleetSpendLimitRead(ORMModel):
    id: uuid.UUID
    fleet_id: uuid.UUID
    period: LimitPeriod
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class OrganizationSpendLimitRead(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    period: LimitPeriod
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime


class FinancialActionRequest(BaseModel):
    agent_id: uuid.UUID
    idempotency_key: str = Field(min_length=1, max_length=100)
    action_type: FinancialActionType
    resource: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    context: dict[str, Any] = Field(default_factory=dict)


class FinancialActionResult(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    agent_id: uuid.UUID
    fleet_id: uuid.UUID
    organization_id: uuid.UUID
    action_type: FinancialActionType
    amount: Decimal
    currency: str
    status: FinancialActionStatus
    allowed: bool
    permission_allowed: bool
    spend_allowed: bool
    policy_id: uuid.UUID | None
    reason: str
    adapter_reference: str | None
    timestamp: datetime
    idempotent_replay: bool = False


class FinancialActionReverseRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=500)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    username: str
    role: Role


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=500)


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=32, max_length=500)


class OverviewRead(BaseModel):
    active_agents: int
    active_fleets: int
    active_policies: int
    emergency_fleets: int
    budget_limit: Decimal
    settled_spend: Decimal
    reserved_spend: Decimal
    recent_decisions: list[FinancialActionResult]
    recent_audits: list["AuditLogRead"]


class AuditLogRead(ORMModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: uuid.UUID | None
    user_reference: uuid.UUID
    username: str
    agent_id: uuid.UUID | None
    agent_reference: uuid.UUID | None
    action: str
    resource: str
    result: str
    policy_id: uuid.UUID | None
    policy_reference: uuid.UUID | None
    request_id: uuid.UUID | None
    fleet_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    amount: Decimal | None
    currency: str | None
    policy_decision: str | None
    spend_decision: str | None
    execution_result: str | None
    correlation_id: str | None
    metadata_json: dict[str, Any]
    decision_context: dict[str, Any]
    policy_version: str | None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
