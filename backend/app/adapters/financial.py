"""Sandbox financial execution adapter."""

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from backend.app.models import FinancialActionType


@dataclass(frozen=True, slots=True)
class AdapterExecution:
    reference: str


class FinancialAdapter(Protocol):
    def execute(
        self,
        *,
        request_id: uuid.UUID,
        action_type: FinancialActionType,
        amount: Decimal,
        currency: str,
        resource: str,
    ) -> AdapterExecution: ...


class SandboxFinancialAdapter:
    """Deterministic adapter that simulates a successful financial operation."""

    def execute(
        self,
        *,
        request_id: uuid.UUID,
        action_type: FinancialActionType,
        amount: Decimal,
        currency: str,
        resource: str,
    ) -> AdapterExecution:
        del amount, currency, resource
        return AdapterExecution(reference=f"sandbox-{action_type.value}-{request_id}")
