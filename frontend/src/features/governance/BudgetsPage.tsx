import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CircleDollarSign, Plus } from "lucide-react";
import { useMemo, useState } from "react";

import { apiRequest } from "../../lib/api/client";
import { DataState, PageHeader, StatusBadge } from "./components";
import type { Agent, FinancialAction, Fleet, Organization, Overview, SpendLimit } from "./types";

export function BudgetsPage() {
  const client = useQueryClient();
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiRequest<Organization[]>("organizations?limit=500"),
  });
  const agentLimits = useQuery({
    queryKey: ["agent-limits"],
    queryFn: () => apiRequest<SpendLimit[]>("spend-limits?limit=500"),
  });
  const fleetLimits = useQuery({
    queryKey: ["fleet-limits"],
    queryFn: () => apiRequest<SpendLimit[]>("fleet-spend-limits?limit=500"),
  });
  const organizationLimits = useQuery({
    queryKey: ["organization-limits"],
    queryFn: () => apiRequest<SpendLimit[]>("organization-spend-limits?limit=500"),
  });
  const actions = useQuery({
    queryKey: ["financial-actions"],
    queryFn: () => apiRequest<FinancialAction[]>("financial-actions?limit=500"),
  });
  const overview = useQuery({
    queryKey: ["overview"],
    queryFn: () => apiRequest<Overview>("overview"),
  });
  const [draft, setDraft] = useState({
    scope: "agent",
    scopeId: "",
    period: "daily",
    amount: "",
    currency: "USD",
  });
  const create = useMutation({
    mutationFn: () => {
      const body = { period: draft.period, amount: draft.amount, currency: draft.currency };
      if (draft.scope === "agent")
        return apiRequest("spend-limits", {
          method: "POST",
          body: JSON.stringify({ ...body, agent_id: draft.scopeId }),
        });
      return apiRequest(`${draft.scope}s/${draft.scopeId}/spend-limits`, {
        method: "POST",
        body: JSON.stringify(body),
      });
    },
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [`${draft.scope}-limits`] });
      setDraft({ ...draft, amount: "" });
    },
  });
  const scopes =
    draft.scope === "agent"
      ? agents.data
      : draft.scope === "fleet"
        ? fleets.data
        : organizations.data;
  const rows = useMemo(
    () => [
      ...(agentLimits.data ?? []).map((item) => ({
        ...item,
        scope: "Agent",
        name: agents.data?.find((agent) => agent.id === item.agent_id)?.name ?? "Agent",
      })),
      ...(fleetLimits.data ?? []).map((item) => ({
        ...item,
        scope: "Fleet",
        name: fleets.data?.find((fleet) => fleet.id === item.fleet_id)?.name ?? "Fleet",
      })),
      ...(organizationLimits.data ?? []).map((item) => ({
        ...item,
        scope: "Organization",
        name:
          organizations.data?.find((org) => org.id === item.organization_id)?.name ??
          "Organization",
      })),
    ],
    [
      agentLimits.data,
      agents.data,
      fleetLimits.data,
      fleets.data,
      organizationLimits.data,
      organizations.data,
    ],
  );
  const totalSettled =
    actions.data
      ?.filter((item) => item.status === "settled")
      .reduce((sum, item) => sum + Number(item.amount), 0) ?? 0;
  const totalReversed =
    actions.data
      ?.filter((item) => item.status === "reversed")
      .reduce((sum, item) => sum + Number(item.amount), 0) ?? 0;

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Spend governance"
        title="Budget management"
        description="Mandatory limits across organization, fleet, and agent scopes."
      />
      <div className="budget-summary">
        <article>
          <CircleDollarSign />
          <span>Settled</span>
          <strong>{totalSettled.toFixed(2)} USD</strong>
        </article>
        <article>
          <CircleDollarSign />
          <span>Reversed</span>
          <strong>{totalReversed.toFixed(2)} USD</strong>
        </article>
        <article>
          <CircleDollarSign />
          <span>Reserved</span>
          <strong>{Number(overview.data?.reserved_spend ?? 0).toFixed(2)} USD</strong>
        </article>
      </div>
      <form
        className="inline-create panel"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <label>
          Scope
          <select
            value={draft.scope}
            onChange={(e) => setDraft({ ...draft, scope: e.target.value, scopeId: "" })}
          >
            <option value="organization">Organization</option>
            <option value="fleet">Fleet</option>
            <option value="agent">Agent</option>
          </select>
        </label>
        <label>
          Target
          <select
            required
            value={draft.scopeId}
            onChange={(e) => setDraft({ ...draft, scopeId: e.target.value })}
          >
            <option value="">Select target</option>
            {scopes?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Period
          <select
            value={draft.period}
            onChange={(e) => setDraft({ ...draft, period: e.target.value })}
          >
            <option value="transaction">Transaction</option>
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
          </select>
        </label>
        <label>
          Amount
          <input
            required
            type="number"
            min="0.01"
            step="0.01"
            value={draft.amount}
            onChange={(e) => setDraft({ ...draft, amount: e.target.value })}
          />
        </label>
        <button className="primary-button">
          <Plus size={16} /> Add budget
        </button>
      </form>
      <DataState
        loading={agentLimits.isLoading || fleetLimits.isLoading || organizationLimits.isLoading}
        error={agentLimits.error ?? fleetLimits.error ?? organizationLimits.error}
        empty={!rows.length}
      >
        <div className="table-shell">
          <table>
            <thead>
              <tr>
                <th>Scope</th>
                <th>Target</th>
                <th>Period</th>
                <th>Limit</th>
                <th>State</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((item) => (
                <tr key={`${item.scope}-${item.id}`}>
                  <td>{item.scope}</td>
                  <td>
                    <strong>{item.name}</strong>
                  </td>
                  <td>{item.period}</td>
                  <td>
                    {item.amount} {item.currency}
                  </td>
                  <td>
                    <StatusBadge value="active" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </div>
  );
}
