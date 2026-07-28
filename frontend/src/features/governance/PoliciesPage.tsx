import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useMemo, useState } from "react";

import { apiRequest } from "../../lib/api/client";
import {
  ConfirmButton,
  DataState,
  Modal,
  MutationError,
  PageHeader,
  StatusBadge,
} from "./components";
import type { Agent, Permission, Policy } from "./types";

const empty = {
  name: "",
  effect: "allow",
  resource: "accounts/operating",
  action: "payment",
  priority: 100,
  conditions: "{}",
  allows_uncapped_spend: false,
};

export function PoliciesPage() {
  const client = useQueryClient();
  const policies = useQuery({
    queryKey: ["policies"],
    queryFn: () => apiRequest<Policy[]>("policies?limit=500"),
  });
  const permissions = useQuery({
    queryKey: ["permissions"],
    queryFn: () => apiRequest<Permission[]>("permissions?limit=500"),
  });
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const [draft, setDraft] = useState(empty);
  const [assignment, setAssignment] = useState({ agent_id: "", policy_id: "" });
  const [editing, setEditing] = useState<Policy | null>(null);
  const [editPriority, setEditPriority] = useState(0);
  const [validationError, setValidationError] = useState("");
  const refresh = () => {
    client.invalidateQueries({ queryKey: ["policies"] });
    client.invalidateQueries({ queryKey: ["permissions"] });
  };
  const create = useMutation({
    mutationFn: () =>
      apiRequest<Policy>("policies", {
        method: "POST",
        body: JSON.stringify({
          ...draft,
          priority: Number(draft.priority),
          conditions: JSON.parse(draft.conditions),
        }),
      }),
    onSuccess: () => {
      setDraft(empty);
      refresh();
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => apiRequest<void>(`policies/${id}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
  const toggle = useMutation({
    mutationFn: (item: Policy) =>
      apiRequest<Policy>(`policies/${item.id}`, {
        method: "PATCH",
        body: JSON.stringify({ enabled: !item.enabled }),
      }),
    onSuccess: refresh,
  });
  const reprioritize = useMutation({
    mutationFn: ({ id, priority }: { id: string; priority: number }) =>
      apiRequest<Policy>(`policies/${id}`, { method: "PATCH", body: JSON.stringify({ priority }) }),
    onSuccess: refresh,
  });
  const assign = useMutation({
    mutationFn: () =>
      apiRequest<Permission>("permissions", { method: "POST", body: JSON.stringify(assignment) }),
    onSuccess: refresh,
  });
  const unassign = useMutation({
    mutationFn: (id: string) => apiRequest<void>(`permissions/${id}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
  const ordered = useMemo(
    () => [...(policies.data ?? [])].sort((a, b) => b.priority - a.priority),
    [policies.data],
  );

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Decision policy"
        title="Policy management"
        description="Configure deterministic allow, deny, and conditional evaluation order."
      />
      <form
        className="policy-form panel"
        onSubmit={(e) => {
          e.preventDefault();
          setValidationError("");
          try {
            const value = JSON.parse(draft.conditions) as unknown;
            if (!value || Array.isArray(value) || typeof value !== "object") {
              setValidationError("Conditions must be a JSON object.");
              return;
            }
            create.mutate();
          } catch {
            setValidationError("Conditions must contain valid JSON.");
          }
        }}
      >
        <label>
          Name
          <input
            required
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
        </label>
        <label>
          Effect
          <select
            value={draft.effect}
            onChange={(e) => setDraft({ ...draft, effect: e.target.value })}
          >
            <option value="allow">Allow</option>
            <option value="deny">Deny</option>
            <option value="conditional">Conditional</option>
          </select>
        </label>
        <label>
          Action
          <input
            value={draft.action}
            onChange={(e) => setDraft({ ...draft, action: e.target.value })}
          />
        </label>
        <label>
          Resource
          <input
            value={draft.resource}
            onChange={(e) => setDraft({ ...draft, resource: e.target.value })}
          />
        </label>
        <label>
          Priority
          <input
            type="number"
            value={draft.priority}
            onChange={(e) => setDraft({ ...draft, priority: Number(e.target.value) })}
          />
        </label>
        <label>
          Conditions JSON
          <input
            value={draft.conditions}
            onChange={(e) => setDraft({ ...draft, conditions: e.target.value })}
          />
        </label>
        <label className="check-field">
          <input
            type="checkbox"
            checked={draft.allows_uncapped_spend}
            onChange={(e) => setDraft({ ...draft, allows_uncapped_spend: e.target.checked })}
          />{" "}
          Explicit uncapped spend
        </label>
        <button className="primary-button">
          <Plus size={16} /> Create policy
        </button>
      </form>
      {validationError && (
        <div className="form-alert" role="alert">
          {validationError}
        </div>
      )}
      <MutationError
        error={
          create.error ??
          remove.error ??
          toggle.error ??
          reprioritize.error ??
          assign.error ??
          unassign.error ??
          null
        }
      />
      <form
        className="assignment-bar panel"
        onSubmit={(e) => {
          e.preventDefault();
          assign.mutate();
        }}
      >
        <strong>Assign policy</strong>
        <select
          required
          value={assignment.agent_id}
          onChange={(e) => setAssignment({ ...assignment, agent_id: e.target.value })}
        >
          <option value="">Agent</option>
          {agents.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <select
          required
          value={assignment.policy_id}
          onChange={(e) => setAssignment({ ...assignment, policy_id: e.target.value })}
        >
          <option value="">Policy</option>
          {ordered.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <button>Assign</button>
      </form>
      <DataState loading={policies.isLoading} error={policies.error} empty={!ordered.length}>
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Order</th>
                <th>Policy</th>
                <th>Scope</th>
                <th>Assignments</th>
                <th>Controls</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((policy, index) => {
                const assigned =
                  permissions.data?.filter((item) => item.policy_id === policy.id) ?? [];
                return (
                  <tr key={policy.id}>
                    <td>
                      #{index + 1}
                      <span>P{policy.priority}</span>
                    </td>
                    <td>
                      <strong>{policy.name}</strong>
                      <StatusBadge value={policy.effect} />
                    </td>
                    <td>
                      <strong>{policy.action}</strong>
                      <span>
                        {policy.resource} · {JSON.stringify(policy.conditions)}
                      </span>
                    </td>
                    <td>
                      {assigned.map((item) => (
                        <button
                          className="assignment-chip"
                          title="Unassign"
                          key={item.id}
                          onClick={() => unassign.mutate(item.id)}
                        >
                          {agents.data?.find((agent) => agent.id === item.agent_id)?.name ??
                            "Agent"}{" "}
                          ×
                        </button>
                      ))}
                    </td>
                    <td className="row-actions">
                      <button
                        aria-label={`Edit ${policy.name}`}
                        onClick={() => {
                          setEditing(policy);
                          setEditPriority(policy.priority);
                        }}
                      >
                        <Pencil size={14} /> Edit priority
                      </button>
                      <button onClick={() => toggle.mutate(policy)}>
                        {policy.enabled ? "Disable" : "Enable"}
                      </button>
                      <ConfirmButton
                        message={`Delete ${policy.name}?`}
                        onConfirm={() => remove.mutate(policy.id)}
                      >
                        <Trash2 size={14} />
                      </ConfirmButton>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </DataState>
      <Modal open={Boolean(editing)} title="Edit policy priority" onClose={() => setEditing(null)}>
        <form
          className="modal-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!editing || !Number.isInteger(editPriority) || editPriority < 0) return;
            reprioritize.mutate(
              { id: editing.id, priority: editPriority },
              { onSuccess: () => setEditing(null) },
            );
          }}
        >
          <label>
            Evaluation priority
            <input
              min="0"
              required
              type="number"
              value={editPriority}
              onChange={(event) => setEditPriority(Number(event.target.value))}
            />
          </label>
          <MutationError error={reprioritize.error} />
          <div className="modal-actions">
            <button type="button" onClick={() => setEditing(null)}>
              Cancel
            </button>
            <button className="primary-button">Save priority</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
