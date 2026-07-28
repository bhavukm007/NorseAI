import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Search } from "lucide-react";
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
import type { Agent, Fleet } from "./types";

export function AgentsPage() {
  const queryClient = useQueryClient();
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [draft, setDraft] = useState({ name: "", agent_type: "payments", fleet_id: "" });
  const [editing, setEditing] = useState<Agent | null>(null);
  const [editDraft, setEditDraft] = useState({ name: "", agent_type: "" });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["agents"] });
  const create = useMutation({
    mutationFn: () =>
      apiRequest<Agent>("agents", {
        method: "POST",
        body: JSON.stringify({ ...draft, fleet_id: draft.fleet_id || null }),
      }),
    onSuccess: () => {
      setDraft({ name: "", agent_type: "payments", fleet_id: "" });
      refresh();
    },
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: object }) =>
      apiRequest<Agent>(`agents/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: refresh,
  });
  const setAgentStatus = useMutation({
    mutationFn: ({ id, value }: { id: string; value: string }) =>
      apiRequest<Agent>(`agents/${id}/${value}`, { method: "POST" }),
    onSuccess: refresh,
  });
  const editAgent = (agent: Agent) => {
    setEditing(agent);
    setEditDraft({ name: agent.name, agent_type: agent.agent_type });
  };
  const rows = useMemo(
    () =>
      (agents.data ?? []).filter(
        (agent) =>
          (!search ||
            `${agent.name} ${agent.agent_type}`.toLowerCase().includes(search.toLowerCase())) &&
          (!status || agent.status === status),
      ),
    [agents.data, search, status],
  );

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Registry"
        title="Financial agents"
        description="Register agents, assign fleets, and control execution eligibility."
      />
      <form
        className="inline-create panel"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <label>
          Agent name
          <input
            required
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
        </label>
        <label>
          Type
          <input
            required
            value={draft.agent_type}
            onChange={(e) => setDraft({ ...draft, agent_type: e.target.value })}
          />
        </label>
        <label>
          Fleet
          <select
            value={draft.fleet_id}
            onChange={(e) => setDraft({ ...draft, fleet_id: e.target.value })}
          >
            <option value="">Unassigned</option>
            {fleets.data?.map((fleet) => (
              <option key={fleet.id} value={fleet.id}>
                {fleet.name}
              </option>
            ))}
          </select>
        </label>
        <button className="primary-button">
          <Plus size={16} /> Create agent
        </button>
      </form>
      <MutationError error={create.error ?? update.error ?? setAgentStatus.error ?? null} />
      <div className="toolbar">
        <label className="search-field">
          <Search size={15} />
          <input
            aria-label="Search agents"
            placeholder="Search agents"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
        <select
          aria-label="Filter agent status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="enabled">Enabled</option>
          <option value="disabled">Disabled</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>
      <DataState
        loading={agents.isLoading || fleets.isLoading}
        error={agents.error ?? fleets.error}
        empty={!rows.length}
      >
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Agent</th>
                <th>Fleet</th>
                <th>Status</th>
                <th>Controls</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((agent) => (
                <tr key={agent.id}>
                  <td>
                    <strong>{agent.name}</strong>
                    <span>{agent.agent_type}</span>
                  </td>
                  <td>
                    <select
                      aria-label={`Fleet for ${agent.name}`}
                      value={agent.fleet_id ?? ""}
                      onChange={(e) =>
                        update.mutate({ id: agent.id, body: { fleet_id: e.target.value || null } })
                      }
                    >
                      <option value="">Unassigned</option>
                      {fleets.data?.map((fleet) => (
                        <option key={fleet.id} value={fleet.id}>
                          {fleet.name}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td>
                    <StatusBadge value={agent.status} />
                  </td>
                  <td className="row-actions">
                    <button aria-label={`Edit ${agent.name}`} onClick={() => editAgent(agent)}>
                      <Pencil size={14} /> Edit
                    </button>
                    <button
                      onClick={() => setAgentStatus.mutate({ id: agent.id, value: "enable" })}
                    >
                      Enable
                    </button>
                    <ConfirmButton
                      message={`Disable ${agent.name}?`}
                      onConfirm={() => setAgentStatus.mutate({ id: agent.id, value: "disable" })}
                    >
                      Disable
                    </ConfirmButton>
                    <ConfirmButton
                      message={`Suspend ${agent.name}?`}
                      onConfirm={() => setAgentStatus.mutate({ id: agent.id, value: "suspend" })}
                    >
                      Suspend
                    </ConfirmButton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
      <Modal open={Boolean(editing)} title="Edit agent" onClose={() => setEditing(null)}>
        <form
          className="modal-form"
          onSubmit={(event) => {
            event.preventDefault();
            if (!editing || !editDraft.name.trim() || !editDraft.agent_type.trim()) return;
            update.mutate(
              {
                id: editing.id,
                body: {
                  name: editDraft.name.trim(),
                  agent_type: editDraft.agent_type.trim(),
                },
              },
              { onSuccess: () => setEditing(null) },
            );
          }}
        >
          <label>
            Agent name
            <input
              required
              value={editDraft.name}
              onChange={(event) => setEditDraft({ ...editDraft, name: event.target.value })}
            />
          </label>
          <label>
            Agent type
            <input
              required
              value={editDraft.agent_type}
              onChange={(event) => setEditDraft({ ...editDraft, agent_type: event.target.value })}
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
