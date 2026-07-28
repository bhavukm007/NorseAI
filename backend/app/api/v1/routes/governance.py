"""Phase 2 governance REST API."""

import csv
import io
import json
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.encoders import jsonable_encoder

from backend.app.api.dependencies import Services, get_services, require_roles
from backend.app.models import AgentStatus, GovernanceStatus, Role
from backend.app.schemas.governance import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    AuditLogRead,
    ErrorResponse,
    EvaluationRequest,
    EvaluationResult,
    FinancialActionRequest,
    FinancialActionResult,
    FinancialActionReverseRequest,
    FleetCreate,
    FleetRead,
    FleetSpendLimitRead,
    FleetUpdate,
    OrganizationCreate,
    OrganizationRead,
    OrganizationSpendLimitRead,
    OrganizationUpdate,
    OverviewRead,
    PermissionCreate,
    PermissionRead,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
    Principal,
    ScopedSpendLimitCreate,
    SpendEvaluationRequest,
    SpendEvaluationResult,
    SpendLimitCreate,
    SpendLimitRead,
    SpendLimitUpdate,
)

ERROR_RESPONSES = {
    401: {"model": ErrorResponse, "description": "Missing or invalid bearer token"},
    403: {"model": ErrorResponse, "description": "Role is not authorized"},
    404: {"model": ErrorResponse, "description": "Resource does not exist"},
    409: {"model": ErrorResponse, "description": "Resource conflict"},
    422: {"model": ErrorResponse, "description": "Request validation failed"},
}
router = APIRouter(tags=["governance"], responses=ERROR_RESPONSES)
ServiceDependency = Annotated[Services, Depends(get_services)]
ReadPrincipal = Annotated[Principal, Depends(require_roles(*list(Role)))]
WritePrincipal = Annotated[Principal, Depends(require_roles(Role.ADMIN, Role.OPERATOR))]
AdminPrincipal = Annotated[Principal, Depends(require_roles(Role.ADMIN))]
AuditPrincipal = Annotated[Principal, Depends(require_roles(Role.ADMIN, Role.AUDITOR))]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=500)]


@router.post("/agents", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(data: AgentCreate, services: ServiceDependency, _: WritePrincipal) -> AgentRead:
    """Create an agent. RBAC: Admin or Operator."""
    return AgentRead.model_validate(services.agents.create(data))


@router.get("/agents", response_model=list[AgentRead])
def list_agents(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[AgentRead]:
    """List agents with offset pagination. RBAC: any authenticated role."""
    return [AgentRead.model_validate(item) for item in services.agents.list(offset, limit)]


@router.get("/agents/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: uuid.UUID, services: ServiceDependency, _: ReadPrincipal) -> AgentRead:
    """Get one agent. RBAC: any authenticated role."""
    return AgentRead.model_validate(services.agents.get(agent_id))


@router.patch("/agents/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> AgentRead:
    """Update an agent. RBAC: Admin or Operator."""
    return AgentRead.model_validate(services.agents.update(agent_id, data))


@router.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(agent_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> Response:
    """Delete an agent. RBAC: Admin."""
    services.agents.delete(agent_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/policies", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
def create_policy(data: PolicyCreate, services: ServiceDependency, _: WritePrincipal) -> PolicyRead:
    """Create a policy. RBAC: Admin or Operator."""
    return PolicyRead.model_validate(services.policies.create(data))


@router.get("/policies", response_model=list[PolicyRead])
def list_policies(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[PolicyRead]:
    """List policies with offset pagination. RBAC: any authenticated role."""
    return [PolicyRead.model_validate(item) for item in services.policies.list(offset, limit)]


@router.get("/policies/{policy_id}", response_model=PolicyRead)
def get_policy(policy_id: uuid.UUID, services: ServiceDependency, _: ReadPrincipal) -> PolicyRead:
    """Get one policy. RBAC: any authenticated role."""
    return PolicyRead.model_validate(services.policies.get(policy_id))


@router.patch("/policies/{policy_id}", response_model=PolicyRead)
def update_policy(
    policy_id: uuid.UUID,
    data: PolicyUpdate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> PolicyRead:
    """Update a policy. RBAC: Admin or Operator."""
    return PolicyRead.model_validate(services.policies.update(policy_id, data))


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_policy(policy_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> Response:
    """Delete a policy. RBAC: Admin."""
    services.policies.delete(policy_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/permissions", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
def assign_permission(
    data: PermissionCreate, services: ServiceDependency, _: WritePrincipal
) -> PermissionRead:
    """Assign a policy to an agent. RBAC: Admin or Operator."""
    return PermissionRead.model_validate(services.permissions.assign(data))


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[PermissionRead]:
    return [
        PermissionRead.model_validate(item) for item in services.permissions.list(offset, limit)
    ]


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def unassign_permission(
    permission_id: uuid.UUID, services: ServiceDependency, _: WritePrincipal
) -> Response:
    services.permissions.unassign(permission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/permissions/evaluate", response_model=EvaluationResult)
def evaluate_permission(
    data: EvaluationRequest, services: ServiceDependency, _: WritePrincipal
) -> EvaluationResult:
    """Evaluate an agent action. RBAC: Admin or Operator."""
    return services.permissions.evaluate(data)


@router.post("/spend-limits", response_model=SpendLimitRead, status_code=status.HTTP_201_CREATED)
def create_limit(
    data: SpendLimitCreate, services: ServiceDependency, _: WritePrincipal
) -> SpendLimitRead:
    """Create a spend limit. RBAC: Admin or Operator."""
    return SpendLimitRead.model_validate(services.spend.create(data))


@router.get("/spend-limits", response_model=list[SpendLimitRead])
def list_limits(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[SpendLimitRead]:
    """List spend limits with offset pagination. RBAC: any authenticated role."""
    return [SpendLimitRead.model_validate(item) for item in services.spend.list(offset, limit)]


@router.get("/spend-limits/{limit_id}", response_model=SpendLimitRead)
def get_limit(limit_id: uuid.UUID, services: ServiceDependency, _: ReadPrincipal) -> SpendLimitRead:
    """Get one spend limit. RBAC: any authenticated role."""
    return SpendLimitRead.model_validate(services.spend.get(limit_id))


@router.patch("/spend-limits/{limit_id}", response_model=SpendLimitRead)
def update_limit(
    limit_id: uuid.UUID,
    data: SpendLimitUpdate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> SpendLimitRead:
    """Update a spend limit. RBAC: Admin or Operator."""
    return SpendLimitRead.model_validate(services.spend.update(limit_id, data))


@router.delete("/spend-limits/{limit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_limit(limit_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> Response:
    """Delete a spend limit. RBAC: Admin."""
    services.spend.delete(limit_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/spend/evaluate", response_model=SpendEvaluationResult)
def evaluate_spend(
    data: SpendEvaluationRequest, services: ServiceDependency, _: WritePrincipal
) -> SpendEvaluationResult:
    """Evaluate and record an allowed transaction. RBAC: Admin or Operator."""
    return services.spend.evaluate(data)


def _status_change(
    agent_id: uuid.UUID,
    value: AgentStatus,
    services: Services,
) -> AgentRead:
    return AgentRead.model_validate(services.emergency.set_status(agent_id, value))


@router.post("/agents/{agent_id}/disable", response_model=AgentRead)
def disable_agent(agent_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> AgentRead:
    """Disable an agent immediately. RBAC: Admin."""
    return _status_change(agent_id, AgentStatus.DISABLED, services)


@router.post("/agents/{agent_id}/enable", response_model=AgentRead)
def enable_agent(agent_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> AgentRead:
    """Enable an agent. RBAC: Admin."""
    return _status_change(agent_id, AgentStatus.ENABLED, services)


@router.post("/agents/{agent_id}/suspend", response_model=AgentRead)
def suspend_agent(agent_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> AgentRead:
    """Suspend an agent immediately. RBAC: Admin."""
    return _status_change(agent_id, AgentStatus.SUSPENDED, services)


@router.get("/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(
    services: ServiceDependency,
    _: AuditPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
    search: str | None = None,
    actor: str | None = None,
    fleet_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    policy_id: uuid.UUID | None = None,
    action: str | None = None,
    result: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[AuditLogRead]:
    """List immutable audit logs. RBAC: Admin or Auditor."""
    return [
        AuditLogRead.model_validate(item)
        for item in services.audit.filtered(
            offset=offset,
            limit=limit,
            search=search,
            actor=actor,
            fleet_id=fleet_id,
            organization_id=organization_id,
            policy_id=policy_id,
            action=action,
            result=result,
            date_from=date_from,
            date_to=date_to,
        )
    ]


@router.get("/audit-logs/export")
def export_audit_logs(
    services: ServiceDependency,
    _: AuditPrincipal,
    format: Annotated[str, Query(pattern="^(csv|jsonl)$")] = "csv",
) -> Response:
    logs = [AuditLogRead.model_validate(item) for item in services.audit.list(0, 500)]
    rows = [jsonable_encoder(item.model_dump()) for item in logs]
    if format == "jsonl":
        body = "\n".join(json.dumps(item) for item in rows)
        return Response(
            body,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": "attachment; filename=audit-logs.jsonl"},
        )
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit-logs.csv"},
    )


@router.post(
    "/organizations",
    response_model=OrganizationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    data: OrganizationCreate, services: ServiceDependency, _: AdminPrincipal
) -> OrganizationRead:
    return OrganizationRead.model_validate(services.fleets.create_organization(data))


@router.get("/organizations", response_model=list[OrganizationRead])
def list_organizations(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[OrganizationRead]:
    return [
        OrganizationRead.model_validate(item)
        for item in services.fleets.list_organizations(offset, limit)
    ]


@router.patch("/organizations/{organization_id}", response_model=OrganizationRead)
def update_organization(
    organization_id: uuid.UUID,
    data: OrganizationUpdate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> OrganizationRead:
    return OrganizationRead.model_validate(
        services.fleets.update_organization(organization_id, data)
    )


def _organization_status_change(
    organization_id: uuid.UUID,
    value: GovernanceStatus,
    services: Services,
) -> OrganizationRead:
    return OrganizationRead.model_validate(
        services.fleets.set_organization_status(organization_id, value)
    )


@router.post("/organizations/{organization_id}/enable", response_model=OrganizationRead)
def enable_organization(
    organization_id: uuid.UUID,
    services: ServiceDependency,
    _: AdminPrincipal,
) -> OrganizationRead:
    return _organization_status_change(organization_id, GovernanceStatus.ENABLED, services)


@router.post("/organizations/{organization_id}/disable", response_model=OrganizationRead)
def disable_organization(
    organization_id: uuid.UUID,
    services: ServiceDependency,
    _: AdminPrincipal,
) -> OrganizationRead:
    return _organization_status_change(organization_id, GovernanceStatus.DISABLED, services)


@router.delete("/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: uuid.UUID,
    services: ServiceDependency,
    _: AdminPrincipal,
) -> Response:
    services.fleets.delete_organization(organization_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/fleets", response_model=FleetRead, status_code=status.HTTP_201_CREATED)
def create_fleet(data: FleetCreate, services: ServiceDependency, _: WritePrincipal) -> FleetRead:
    return FleetRead.model_validate(services.fleets.create(data))


@router.get("/fleets", response_model=list[FleetRead])
def list_fleets(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[FleetRead]:
    return [FleetRead.model_validate(item) for item in services.fleets.list(offset, limit)]


@router.get("/fleets/{fleet_id}", response_model=FleetRead)
def get_fleet(fleet_id: uuid.UUID, services: ServiceDependency, _: ReadPrincipal) -> FleetRead:
    return FleetRead.model_validate(services.fleets.get(fleet_id))


@router.patch("/fleets/{fleet_id}", response_model=FleetRead)
def update_fleet(
    fleet_id: uuid.UUID,
    data: FleetUpdate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> FleetRead:
    return FleetRead.model_validate(services.fleets.update(fleet_id, data))


def _fleet_status_change(
    fleet_id: uuid.UUID, value: GovernanceStatus, services: Services
) -> FleetRead:
    return FleetRead.model_validate(services.fleets.set_status(fleet_id, value))


@router.post("/fleets/{fleet_id}/enable", response_model=FleetRead)
def enable_fleet(fleet_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> FleetRead:
    return _fleet_status_change(fleet_id, GovernanceStatus.ENABLED, services)


@router.post("/fleets/{fleet_id}/disable", response_model=FleetRead)
def disable_fleet(fleet_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal) -> FleetRead:
    return _fleet_status_change(fleet_id, GovernanceStatus.DISABLED, services)


@router.post("/fleets/{fleet_id}/emergency-stop", response_model=FleetRead)
def emergency_stop_fleet(
    fleet_id: uuid.UUID, services: ServiceDependency, _: AdminPrincipal
) -> FleetRead:
    return _fleet_status_change(fleet_id, GovernanceStatus.EMERGENCY_STOPPED, services)


@router.post(
    "/fleets/{fleet_id}/spend-limits",
    response_model=FleetSpendLimitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_fleet_limit(
    fleet_id: uuid.UUID,
    data: ScopedSpendLimitCreate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> FleetSpendLimitRead:
    return FleetSpendLimitRead.model_validate(services.budgets.create_fleet_limit(fleet_id, data))


@router.get("/fleet-spend-limits", response_model=list[FleetSpendLimitRead])
def list_fleet_limits(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[FleetSpendLimitRead]:
    return [
        FleetSpendLimitRead.model_validate(item)
        for item in services.budgets.list_fleet_limits(offset, limit)
    ]


@router.post(
    "/organizations/{organization_id}/spend-limits",
    response_model=OrganizationSpendLimitRead,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_limit(
    organization_id: uuid.UUID,
    data: ScopedSpendLimitCreate,
    services: ServiceDependency,
    _: WritePrincipal,
) -> OrganizationSpendLimitRead:
    return OrganizationSpendLimitRead.model_validate(
        services.budgets.create_organization_limit(organization_id, data)
    )


@router.get(
    "/organization-spend-limits",
    response_model=list[OrganizationSpendLimitRead],
)
def list_organization_limits(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[OrganizationSpendLimitRead]:
    return [
        OrganizationSpendLimitRead.model_validate(item)
        for item in services.budgets.list_organization_limits(offset, limit)
    ]


@router.post("/financial-actions", response_model=FinancialActionResult)
def execute_financial_action(
    data: FinancialActionRequest,
    services: ServiceDependency,
    _: WritePrincipal,
) -> FinancialActionResult:
    """Execute payment, transfer, or refund through mandatory governance."""
    return services.financial_actions.execute(data)


@router.get("/financial-actions", response_model=list[FinancialActionResult])
def list_financial_actions(
    services: ServiceDependency,
    _: ReadPrincipal,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[FinancialActionResult]:
    return services.financial_actions.list(offset, limit)


@router.post("/financial-actions/{action_id}/reverse", response_model=FinancialActionResult)
def reverse_financial_action(
    action_id: uuid.UUID,
    data: FinancialActionReverseRequest,
    services: ServiceDependency,
    _: AdminPrincipal,
) -> FinancialActionResult:
    return services.financial_actions.reverse(action_id, data.reason)


@router.get("/overview", response_model=OverviewRead)
def governance_overview(services: ServiceDependency, _: ReadPrincipal) -> OverviewRead:
    return services.overview.get()
