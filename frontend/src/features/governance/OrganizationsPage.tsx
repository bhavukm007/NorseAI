import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { apiRequest } from "../../lib/api/client";
import {
  ConfirmButton,
  DataState,
  Modal,
  MutationError,
  PageHeader,
  StatusBadge,
} from "./components";
import type { Fleet, Organization } from "./types";

export function OrganizationsPage() {
  const queryClient = useQueryClient();
  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiRequest<Organization[]>("organizations?limit=500"),
  });
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const [search, setSearch] = useState("");
  const [name, setName] = useState("");
  const [editing, setEditing] = useState<Organization | null>(null);
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["organizations"] });
  const create = useMutation({
    mutationFn: () =>
      apiRequest<Organization>("organizations", {
        method: "POST",
        body: JSON.stringify({ name: name.trim() }),
      }),
    onSuccess: () => {
      setName("");
      refresh();
    },
  });
  const update = useMutation({
    mutationFn: ({ id, nextName }: { id: string; nextName: string }) =>
      apiRequest<Organization>(`organizations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ name: nextName.trim() }),
      }),
    onSuccess: () => {
      setEditing(null);
      refresh();
    },
  });
  const setStatus = useMutation({
    mutationFn: ({ id, action }: { id: string; action: "enable" | "disable" }) =>
      apiRequest<Organization>(`organizations/${id}/${action}`, { method: "POST" }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: (id: string) =>
      apiRequest<void>(`organizations/${id}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      refresh();
      queryClient.invalidateQueries({ queryKey: ["fleets"] });
    },
  });
  const rows = useMemo(
    () =>
      (organizations.data ?? []).filter((organization) =>
        organization.name.toLowerCase().includes(search.trim().toLowerCase()),
      ),
    [organizations.data, search],
  );
  const mutationError = create.error ?? update.error ?? setStatus.error ?? remove.error ?? null;

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Governance scope"
        title="Organizations"
        description="Create and control the organization boundary above financial-agent fleets."
      />
      <form
        className="inline-create panel"
        onSubmit={(event) => {
          event.preventDefault();
          if (name.trim()) create.mutate();
        }}
      >
        <label>
          Organization name
          <input
            required
            maxLength={150}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <button className="primary-button" disabled={!name.trim() || create.isPending}>
          <Plus size={16} /> Create organization
        </button>
      </form>
      <MutationError error={mutationError} />
      <div className="toolbar">
        <label className="search-field">
          <Search size={15} aria-hidden="true" />
          <input
            aria-label="Search organizations"
            placeholder="Search organizations"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
      </div>
      <DataState
        loading={organizations.isLoading || fleets.isLoading}
        error={organizations.error ?? fleets.error}
        empty={!rows.length}
      >
        <div className="card-grid">
          {rows.map((organization) => {
            const fleetCount =
              fleets.data?.filter((fleet) => fleet.organization_id === organization.id).length ?? 0;
            return (
              <article className="entity-card panel" key={organization.id}>
                <div className="entity-card-header">
                  <div>
                    <span className="section-label">Organization</span>
                    <h2>{organization.name}</h2>
                  </div>
                  <StatusBadge value={organization.status} />
                </div>
                <dl>
                  <div>
                    <dt>Fleets</dt>
                    <dd>{fleetCount}</dd>
                  </div>
                </dl>
                <div className="row-actions">
                  <button
                    aria-label={`Edit ${organization.name}`}
                    type="button"
                    onClick={() => setEditing(organization)}
                  >
                    <Pencil size={14} /> Edit
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setStatus.mutate({
                        id: organization.id,
                        action: organization.status === "enabled" ? "disable" : "enable",
                      })
                    }
                  >
                    {organization.status === "enabled" ? "Disable" : "Enable"}
                  </button>
                  <ConfirmButton
                    className="danger-button"
                    message={`Delete ${organization.name}? Its fleets must not contain protected financial history.`}
                    onConfirm={() => remove.mutate(organization.id)}
                  >
                    <Trash2 size={14} /> Delete
                  </ConfirmButton>
                </div>
              </article>
            );
          })}
        </div>
      </DataState>
      <OrganizationEditor
        organization={editing}
        error={update.error}
        onClose={() => setEditing(null)}
        onSave={(nextName) => {
          if (editing) update.mutate({ id: editing.id, nextName });
        }}
      />
    </div>
  );
}

function OrganizationEditor({
  organization,
  error,
  onClose,
  onSave,
}: {
  organization: Organization | null;
  error: Error | null;
  onClose: () => void;
  onSave: (name: string) => void;
}) {
  const [name, setName] = useState(organization?.name ?? "");
  useEffect(() => setName(organization?.name ?? ""), [organization]);

  return (
    <Modal open={Boolean(organization)} title="Edit organization" onClose={onClose}>
      <form
        className="modal-form"
        onSubmit={(event) => {
          event.preventDefault();
          if (name.trim()) onSave(name);
        }}
      >
        <label>
          Organization name
          <input
            autoFocus
            required
            maxLength={150}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <MutationError error={error} />
        <div className="modal-actions">
          <button type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="primary-button" disabled={!name.trim()}>
            Save changes
          </button>
        </div>
      </form>
    </Modal>
  );
}
