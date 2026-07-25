"""Organization and fleet governance administration."""

import uuid

from backend.app.models import Fleet, GovernanceStatus, Organization
from backend.app.schemas.governance import FleetCreate, FleetUpdate, OrganizationCreate
from backend.app.services.base import Service


class FleetService(Service):
    def create_organization(self, data: OrganizationCreate) -> Organization:
        organization = self.repos.organizations.add(Organization(name=data.name.strip()))
        self.audit.record("organization.create", f"organizations/{organization.id}")
        return organization

    def create(self, data: FleetCreate) -> Fleet:
        if not self.repos.organizations.get(data.organization_id):
            raise self.not_found("Organization")
        fleet = self.repos.fleets.add(
            Fleet(organization_id=data.organization_id, name=data.name.strip())
        )
        self.audit.record(
            "fleet.create",
            f"fleets/{fleet.id}",
            fleet_id=fleet.id,
            organization_id=fleet.organization_id,
        )
        return fleet

    def list_organizations(self, offset: int, limit: int) -> list[Organization]:
        return self.repos.organizations.list(offset, limit)

    def list(self, offset: int, limit: int) -> list[Fleet]:
        return self.repos.fleets.list(offset, limit)

    def get(self, fleet_id: uuid.UUID) -> Fleet:
        fleet = self.repos.fleets.get(fleet_id)
        if not fleet:
            raise self.not_found("Fleet")
        return fleet

    def set_status(self, fleet_id: uuid.UUID, value: GovernanceStatus) -> Fleet:
        fleet = self.get(fleet_id)
        fleet.status = value
        self.repos.session.flush()
        self.audit.record(
            f"fleet.{value.value}",
            f"fleets/{fleet.id}",
            fleet_id=fleet.id,
            organization_id=fleet.organization_id,
        )
        return fleet

    def update(self, fleet_id: uuid.UUID, data: FleetUpdate) -> Fleet:
        fleet = self.get(fleet_id)
        values = data.model_dump(exclude_unset=True)
        if "organization_id" in values and not self.repos.organizations.get(
            values["organization_id"]
        ):
            raise self.not_found("Organization")
        for key, value in values.items():
            setattr(fleet, key, value)
        self.repos.session.flush()
        self.audit.record(
            "fleet.update",
            f"fleets/{fleet.id}",
            fleet_id=fleet.id,
            organization_id=fleet.organization_id,
        )
        return fleet
