"""Validated Phase 2 API contracts."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models import AgentStatus, LimitPeriod, PolicyEffect, Role


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Principal(BaseModel):
    id: uuid.UUID | None = None
    username: str
    role: Role


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=2000)
    owner_id: uuid.UUID | None = None
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
    agent_type: str | None = Field(default=None, min_length=1, max_length=100)


class AgentRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    owner_id: uuid.UUID | None
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


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    effect: PolicyEffect | None = None
    resource: str | None = Field(default=None, min_length=1, max_length=200)
    action: str | None = Field(default=None, min_length=1, max_length=100)
    conditions: dict[str, Any] | None = None
    priority: int | None = Field(default=None, ge=0, le=1_000_000)
    enabled: bool | None = None


class PolicyRead(ORMModel):
    id: uuid.UUID
    name: str
    effect: PolicyEffect
    resource: str
    action: str
    conditions: dict[str, Any]
    priority: int
    enabled: bool
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


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
