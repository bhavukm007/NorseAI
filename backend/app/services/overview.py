"""Live operator dashboard aggregates."""

from decimal import Decimal

from sqlalchemy import func, select

from backend.app.models import (
    Agent,
    AgentStatus,
    BudgetReservation,
    FinancialAction,
    FinancialActionStatus,
    Fleet,
    FleetSpendLimit,
    GovernanceStatus,
    OrganizationSpendLimit,
    Policy,
    ReservationStatus,
    SpendLimit,
    SpendRecord,
    SpendRecordType,
)
from backend.app.schemas.governance import (
    AuditLogRead,
    FinancialActionResult,
    OverviewRead,
)
from backend.app.services.base import Service


class OverviewService(Service):
    def get(self) -> OverviewRead:
        session = self.repos.session

        def count(model, condition) -> int:
            value = session.scalar(select(func.count()).select_from(model).where(condition))
            return int(value or 0)

        budget_limit = Decimal(
            session.scalar(
                select(
                    func.coalesce(select(func.sum(SpendLimit.amount)).scalar_subquery(), 0)
                    + func.coalesce(select(func.sum(FleetSpendLimit.amount)).scalar_subquery(), 0)
                    + func.coalesce(
                        select(func.sum(OrganizationSpendLimit.amount)).scalar_subquery(), 0
                    )
                )
            )
            or 0
        )
        settled_spend = Decimal(
            session.scalar(
                select(func.coalesce(func.sum(SpendRecord.amount), 0)).where(
                    SpendRecord.record_type == SpendRecordType.SETTLEMENT
                )
            )
            or 0
        ) - Decimal(
            session.scalar(
                select(func.coalesce(func.sum(SpendRecord.amount), 0)).where(
                    SpendRecord.record_type == SpendRecordType.REVERSAL
                )
            )
            or 0
        )
        reserved_spend = Decimal(
            session.scalar(
                select(func.coalesce(func.sum(BudgetReservation.amount), 0)).where(
                    BudgetReservation.status == ReservationStatus.RESERVED
                )
            )
            or 0
        )
        actions = list(
            session.scalars(
                select(FinancialAction).order_by(FinancialAction.timestamp.desc()).limit(8)
            )
        )
        audits = self.repos.list_audits(0, 8)
        return OverviewRead(
            active_agents=count(Agent, Agent.status == AgentStatus.ENABLED),
            active_fleets=count(Fleet, Fleet.status == GovernanceStatus.ENABLED),
            active_policies=count(Policy, Policy.enabled.is_(True)),
            emergency_fleets=count(Fleet, Fleet.status == GovernanceStatus.EMERGENCY_STOPPED),
            budget_limit=budget_limit,
            settled_spend=settled_spend,
            reserved_spend=reserved_spend,
            recent_decisions=[
                FinancialActionResult(
                    id=item.id,
                    request_id=item.request_id,
                    agent_id=item.agent_id,
                    fleet_id=item.fleet_id,
                    organization_id=item.organization_id,
                    action_type=item.action_type,
                    amount=item.amount,
                    currency=item.currency,
                    status=item.status,
                    allowed=item.status == FinancialActionStatus.SETTLED,
                    permission_allowed=item.permission_allowed,
                    spend_allowed=item.spend_allowed,
                    policy_id=item.policy_id,
                    reason=item.decision_reason,
                    adapter_reference=item.adapter_reference,
                    timestamp=item.timestamp,
                )
                for item in actions
            ],
            recent_audits=[AuditLogRead.model_validate(item) for item in audits],
        )
