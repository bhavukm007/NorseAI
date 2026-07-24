"""Phase 2 governance REST API."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from backend.app.api.dependencies import Services, get_services, require_roles
from backend.app.models import AgentStatus, Role
from backend.app.schemas.governance import (
    AgentCreate,
    AgentRead,
    AgentUpdate,
    AuditLogRead,
    ErrorResponse,
    EvaluationRequest,
    EvaluationResult,
    PermissionCreate,
    PermissionRead,
    PolicyCreate,
    PolicyRead,
    PolicyUpdate,
    Principal,
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
) -> list[AuditLogRead]:
    """List immutable audit logs. RBAC: Admin or Auditor."""
    return [AuditLogRead.model_validate(item) for item in services.audit.list(offset, limit)]
