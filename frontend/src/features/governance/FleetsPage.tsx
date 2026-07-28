import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus } from "lucide-react";
import { useState } from "react";

import { apiRequest } from "../../lib/api/client";
import {
  ConfirmButton,
  DataState,
  Modal,
  MutationError,
  PageHeader,
  StatusBadge,
} from "./components";
import type { Agent, FinancialAction, Fleet, Organization, SpendLimit } from "./types";

export function FleetsPage() {
  const client = useQueryClient();
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiRequest<Organization[]>("organizations?limit=500"),
  });
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const actions = useQuery({
    queryKey: ["financial-actions"],
    queryFn: () => apiRequest<FinancialAction[]>("financial-actions?limit=500"),
  });
  const limits = useQuery({
    queryKey: ["fleet-limits"],
    queryFn: () => apiRequest<SpendLimit[]>("fleet-spend-limits?limit=500"),
  });
  const [draft, setDraft] = useState({ name: "", organization_id: "" });
  const [editing, setEditing] = useState<Fleet | null>(null);
  const [editName, setEditName] = useState("");
  const refresh = () => client.invalidateQueries({ queryKey: ["fleets"] });
  const create = useMutation({
    mutationFn: () => apiRequest<Fleet>("fleets", { method: "POST", body: JSON.stringify(draft) }),
    onSuccess: () => {
      setDraft({ name: "", organization_id: "" });
      refresh();
    },
  });
  const update = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      apiRequest<Fleet>(`fleets/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
    onSuccess: refresh,
  });
  const status = useMutation({
    mutationFn: ({ id, action }: { id: string; action: string }) =>
      apiRequest<Fleet>(`fleets/${id}/${action}`, { method: "POST" }),
    onSuccess: refresh,
  });

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Fleet governance"
        title="Financial agent fleets"
        description="Manage fleet membership, budgets, and fleet-wide enforcement state."
      />
      <form
        className="inline-create panel"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <label>
          Fleet name
          <input
            required
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
        </label>
        <label>
          Organization
          <select
            required
            value={draft.organization_id}
            onChange={(e) => setDraft({ ...draft, organization_id: e.target.value })}
          >
            <option value="">Select organization</option>
            {organizations.data?.map((item) => (
              <option value={item.id} key={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button">
          <Plus size={16} /> Create fleet
        </button>
      </form>
      <MutationError error={create.error ?? update.error ?? status.error ?? null} />
      <DataState loading={fleets.isLoading} error={fleets.error} empty={!fleets.data?.length}>
        <div className="card-grid">
          {fleets.data?.map((fleet) => {
            const members = agents.data?.filter((agent) => agent.fleet_id === fleet.id) ?? [];
            const settled =
              actions.data
                ?.filter((action) => action.fleet_id === fleet.id && action.status === "settled")
                .reduce((sum, item) => sum + Number(item.amount), 0) ?? 0;
            const budget =
              limits.data
                ?.filter((limit) => limit.fleet_id === fleet.id)
                .reduce((sum, item) => sum + Number(item.amount), 0) ?? 0;
            return (
              <article className="entity-card panel" key={fleet.id}>
                <div className="entity-card-header">
                  <div>
                    <span className="section-label">
                      {organizations.data?.find((item) => item.id === fleet.organization_id)
                        ?.name ?? "Organization"}
                    </span>
                    <h2>{fleet.name}</h2>
                  </div>
                  <StatusBadge value={fleet.status} />
                </div>
                <dl>
                  <div>
                    <dt>Members</dt>
                    <dd>{members.length}</dd>
                  </div>
                  <div>
                    <dt>Budget usage</dt>
                    <dd>
                      {settled.toFixed(2)} / {budget.toFixed(2)} USD
                    </dd>
                  </div>
                </dl>
                <div className="member-list">
                  {members.slice(0, 4).map((agent) => (
                    <span key={agent.id}>{agent.name}</span>
                  ))}
                  {!members.length && <span>No members assigned</span>}
                </div>
                <div className="row-actions">
                  <button
                    aria-label={`Edit ${fleet.name}`}
                    onClick={() => {
                      setEditing(fleet);
                      setEditName(fleet.name);
                    }}
                  >
                    <Pencil size={14} /> Edit
                  </button>
                  <button onClick={() => status.mutate({ id: fleet.id, action: "enable" })}>
                    Recover
                  </button>
                  <ConfirmButton
                    message={`Disable ${fleet.name}?`}
                    onConfirm={() => status.mutate({ id: fleet.id, action: "disable" })}
                  >
                    Disable
                  </ConfirmButton>
                  <ConfirmButton
                    className="danger-button"
                    message={`Emergency stop ${fleet.name}? All governed actions will be blocked.`}
                    onConfirm={() => status.mutate({ id: fleet.id, action: "emergency-stop" })}
                  >
                    Emergency stop
                  </ConfirmButton>
                </div>
              </article>
            );
          })}
        </div>
      </DataState>
      <Modal open={Boolean(editing)} title="Edit fleet" onClose={() => setEditing(null)}>
        <form
          className="modal-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!editing || !editName.trim()) return;
            update.mutate(
              { id: editing.id, name: editName.trim() },
              { onSuccess: () => setEditing(null) },
            );
          }}
        >
          <label>
            Fleet name
            <input
              required
              value={editName}
              onChange={(event) => setEditName(event.target.value)}
            />
          </label>
          <MutationError error={update.error} />
          <div className="modal-actions">
            <button type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
            <button className="primary-button">Save changes</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
