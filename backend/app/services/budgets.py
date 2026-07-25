"""Mandatory agent, fleet, and organization budget enforcement."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.app.models import (
    BudgetReservation,
    FleetSpendLimit,
    LimitPeriod,
    OrganizationSpendLimit,
    ReservationStatus,
)
from backend.app.schemas.governance import ScopedSpendLimitCreate
from backend.app.services.base import Service
from backend.app.services.spend import PERIOD_ORDER, SpendService


class BudgetDecision:
    def __init__(self, allowed: bool, reason: str, remaining: Decimal | None = None) -> None:
        self.allowed = allowed
        self.reason = reason
        self.remaining = remaining


class BudgetService(Service):
    def list_fleet_limits(self, offset: int, limit: int) -> list[FleetSpendLimit]:
        return self.repos.fleet_spend_limits.list(offset, limit)

    def list_organization_limits(self, offset: int, limit: int) -> list[OrganizationSpendLimit]:
        return self.repos.organization_spend_limits.list(offset, limit)

    def create_fleet_limit(
        self, fleet_id: uuid.UUID, data: ScopedSpendLimitCreate
    ) -> FleetSpendLimit:
        fleet = self.repos.fleets.get(fleet_id)
        if not fleet:
            raise self.not_found("Fleet")
        limit = self.repos.fleet_spend_limits.add(
            FleetSpendLimit(fleet_id=fleet_id, **data.model_dump())
        )
        self.audit.record(
            "fleet_spend_limit.create",
            f"fleet-spend-limits/{limit.id}",
            fleet_id=fleet_id,
            organization_id=fleet.organization_id,
        )
        return limit

    def create_organization_limit(
        self, organization_id: uuid.UUID, data: ScopedSpendLimitCreate
    ) -> OrganizationSpendLimit:
        if not self.repos.organizations.get(organization_id):
            raise self.not_found("Organization")
        limit = self.repos.organization_spend_limits.add(
            OrganizationSpendLimit(organization_id=organization_id, **data.model_dump())
        )
        self.audit.record(
            "organization_spend_limit.create",
            f"organization-spend-limits/{limit.id}",
            organization_id=organization_id,
        )
        return limit

    def reserve(
        self,
        *,
        financial_action_id: uuid.UUID,
        agent_id: uuid.UUID,
        fleet_id: uuid.UUID,
        organization_id: uuid.UUID,
        amount: Decimal,
        currency: str,
        timestamp: datetime,
        allow_uncapped: bool,
    ) -> tuple[BudgetDecision, BudgetReservation | None]:
        scoped_limits: list[tuple[str, uuid.UUID, list[Any]]] = [
            ("agent", agent_id, self.repos.limits_for_agent(agent_id, currency)),
            ("fleet", fleet_id, self.repos.limits_for_fleet(fleet_id, currency)),
            (
                "organization",
                organization_id,
                self.repos.limits_for_organization(organization_id, currency),
            ),
        ]
        missing = [scope for scope, _, limits in scoped_limits if not limits]
        if missing and not allow_uncapped:
            return (
                BudgetDecision(
                    False,
                    f"Mandatory {'/'.join(missing)} budget is not configured",
                ),
                None,
            )

        remaining_values: list[Decimal] = []
        for scope, scope_id, limits in scoped_limits:
            for limit in sorted(limits, key=lambda item: PERIOD_ORDER[item.period]):
                if limit.period == LimitPeriod.TRANSACTION:
                    used = Decimal("0")
                else:
                    window = SpendService._window(limit.period, timestamp)
                    assert window is not None
                    used = (
                        self.repos.spent_between(agent_id, currency, window[0], window[1])
                        if scope == "agent"
                        else self.repos.scoped_spent_between(
                            scope, scope_id, currency, window[0], window[1]
                        )
                    )
                    used += self.repos.active_reserved(scope, scope_id, currency)
                remaining = limit.amount - used
                if amount > remaining:
                    return (
                        BudgetDecision(
                            False,
                            f"{scope.title()} {limit.period.value} budget exceeded",
                            max(remaining, Decimal("0")),
                        ),
                        None,
                    )
                remaining_values.append(remaining - amount)

        reservation = self.repos.budget_reservations.add(
            BudgetReservation(
                financial_action_id=financial_action_id,
                agent_id=agent_id,
                fleet_id=fleet_id,
                organization_id=organization_id,
                amount=amount,
                currency=currency,
                status=ReservationStatus.RESERVED,
            )
        )
        remaining = min(remaining_values) if remaining_values else None
        return (
            BudgetDecision(True, "Action is within all mandatory budgets", remaining),
            reservation,
        )
