"""Mandatory governed financial-action execution."""

import uuid

from backend.app.adapters.financial import FinancialAdapter
from backend.app.errors import AppError
from backend.app.models import (
    AgentStatus,
    FinancialAction,
    FinancialActionStatus,
    GovernanceStatus,
    ReservationStatus,
    SpendRecord,
    SpendRecordType,
    utcnow,
)
from backend.app.schemas.governance import (
    EvaluationRequest,
    FinancialActionRequest,
    FinancialActionResult,
)
from backend.app.services.base import Service
from backend.app.services.budgets import BudgetService
from backend.app.services.permissions import PermissionService


class FinancialActionService(Service):
    def __init__(self, repositories, principal, adapter: FinancialAdapter) -> None:
        super().__init__(repositories, principal)
        self.adapter = adapter

    def list(self, offset: int, limit: int) -> list[FinancialActionResult]:
        return [self._result(item) for item in self.repos.financial_actions.list(offset, limit)]

    def execute(self, data: FinancialActionRequest) -> FinancialActionResult:
        replay = self.repos.financial_action_by_idempotency(data.agent_id, data.idempotency_key)
        if replay:
            return self._result(replay, idempotent_replay=True)

        agent = self.repos.agents.get(data.agent_id)
        if not agent:
            raise self.not_found("Agent")
        if not agent.fleet_id or not agent.fleet:
            raise AppError("fleet_required", "Agent must belong to a fleet", 409)
        fleet = agent.fleet
        organization = fleet.organization
        timestamp = utcnow()

        permission = PermissionService(self.repos, self.principal).evaluate(
            EvaluationRequest(
                agent_id=agent.id,
                action=data.action_type.value,
                resource=data.resource,
                context={
                    **data.context,
                    "amount": str(data.amount),
                    "currency": data.currency,
                },
            )
        )
        status_reason = self._status_reason(agent.status, fleet.status, organization.status)
        permission_allowed = permission.allowed and status_reason is None
        policy = (
            self.repos.policies.get(permission.enforced_by_policy)
            if permission.enforced_by_policy
            else None
        )
        action = self.repos.financial_actions.add(
            FinancialAction(
                idempotency_key=data.idempotency_key,
                actor=self.principal.username,
                agent_id=agent.id,
                fleet_id=fleet.id,
                organization_id=organization.id,
                action_type=data.action_type,
                resource=data.resource,
                amount=data.amount,
                currency=data.currency,
                status=FinancialActionStatus.REJECTED,
                permission_allowed=permission_allowed,
                spend_allowed=False,
                policy_id=permission.enforced_by_policy,
                decision_reason=status_reason or permission.reason,
                timestamp=timestamp,
            )
        )

        if not permission_allowed:
            return self._reject(
                action,
                status_reason or permission.reason,
                policy_decision="denied",
                spend_decision="not_evaluated",
            )

        budget = BudgetService(self.repos, self.principal)
        spend, reservation = budget.reserve(
            financial_action_id=action.id,
            agent_id=agent.id,
            fleet_id=fleet.id,
            organization_id=organization.id,
            amount=data.amount,
            currency=data.currency,
            timestamp=timestamp,
            allow_uncapped=bool(policy and policy.allows_uncapped_spend),
        )
        action.spend_allowed = spend.allowed
        action.decision_reason = spend.reason
        self.repos.session.flush()
        if not spend.allowed or not reservation:
            return self._reject(
                action,
                spend.reason,
                policy_decision="allowed",
                spend_decision="denied",
            )

        status_reason = self._status_reason(agent.status, fleet.status, organization.status)
        if status_reason:
            reservation.status = ReservationStatus.RELEASED
            action.spend_allowed = False
            return self._reject(
                action,
                status_reason,
                policy_decision="allowed",
                spend_decision="released",
            )

        execution = self.adapter.execute(
            request_id=action.request_id,
            action_type=data.action_type,
            amount=data.amount,
            currency=data.currency,
            resource=data.resource,
        )
        reservation.status = ReservationStatus.SETTLED
        action.status = FinancialActionStatus.SETTLED
        action.adapter_reference = execution.reference
        action.decision_reason = "Governance approved and sandbox execution settled"
        self.repos.spend_records.add(
            SpendRecord(
                agent_id=agent.id,
                financial_action_id=action.id,
                amount=data.amount,
                currency=data.currency,
                record_type=SpendRecordType.SETTLEMENT,
                timestamp=timestamp,
            )
        )
        self.repos.session.flush()
        self._audit(action, "allowed", "allowed", "settled")
        return self._result(action)

    def reverse(self, action_id: uuid.UUID, reason: str) -> FinancialActionResult:
        action = self.repos.financial_actions.get(action_id)
        if not action:
            raise self.not_found("Financial action")
        if action.status != FinancialActionStatus.SETTLED:
            raise AppError("action_not_reversible", "Only settled actions can be reversed", 409)
        reservation = (
            self.repos.session.query(self.repos.budget_reservations.model)
            .filter_by(financial_action_id=action.id)
            .one()
        )
        reservation.status = ReservationStatus.REVERSED
        action.status = FinancialActionStatus.REVERSED
        action.decision_reason = reason
        self.repos.spend_records.add(
            SpendRecord(
                agent_id=action.agent_id,
                financial_action_id=action.id,
                amount=action.amount,
                currency=action.currency,
                record_type=SpendRecordType.REVERSAL,
                timestamp=utcnow(),
            )
        )
        self.repos.session.flush()
        self._audit(action, "allowed", "reversed", "reversed")
        return self._result(action)

    @staticmethod
    def _status_reason(agent_status, fleet_status, organization_status) -> str | None:
        if agent_status != AgentStatus.ENABLED:
            return f"Agent is {agent_status.value}"
        if fleet_status != GovernanceStatus.ENABLED:
            return f"Fleet is {fleet_status.value}"
        if organization_status != GovernanceStatus.ENABLED:
            return f"Organization is {organization_status.value}"
        return None

    def _reject(
        self,
        action: FinancialAction,
        reason: str,
        *,
        policy_decision: str,
        spend_decision: str,
    ) -> FinancialActionResult:
        action.status = FinancialActionStatus.REJECTED
        action.decision_reason = reason
        self.repos.session.flush()
        self._audit(action, policy_decision, spend_decision, "rejected")
        return self._result(action)

    def _audit(
        self,
        action: FinancialAction,
        policy_decision: str,
        spend_decision: str,
        execution_result: str,
    ) -> None:
        self.audit.record(
            "financial_action.execute",
            action.resource,
            result=execution_result,
            agent_id=action.agent_id,
            policy_id=action.policy_id,
            request_id=action.request_id,
            fleet_id=action.fleet_id,
            organization_id=action.organization_id,
            amount=action.amount,
            currency=action.currency,
            policy_decision=policy_decision,
            spend_decision=spend_decision,
            execution_result=execution_result,
            decision_context={
                "action_type": action.action_type.value,
                "resource": action.resource,
                "amount": str(action.amount),
                "currency": action.currency,
                "permission_allowed": action.permission_allowed,
                "spend_allowed": action.spend_allowed,
            },
            policy_version=(
                str(self.repos.policies.get(action.policy_id).updated_at)
                if action.policy_id
                else None
            ),
        )

    @staticmethod
    def _result(
        action: FinancialAction, *, idempotent_replay: bool = False
    ) -> FinancialActionResult:
        return FinancialActionResult(
            id=action.id,
            request_id=action.request_id,
            agent_id=action.agent_id,
            fleet_id=action.fleet_id,
            organization_id=action.organization_id,
            action_type=action.action_type,
            amount=action.amount,
            currency=action.currency,
            status=action.status,
            allowed=action.status == FinancialActionStatus.SETTLED,
            permission_allowed=action.permission_allowed,
            spend_allowed=action.spend_allowed,
            policy_id=action.policy_id,
            reason=action.decision_reason,
            adapter_reference=action.adapter_reference,
            timestamp=action.timestamp,
            idempotent_replay=idempotent_replay,
        )
