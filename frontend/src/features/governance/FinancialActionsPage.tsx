import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeftRight, RotateCcw, Send } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "../../lib/api/client";
import { ConfirmButton, DataState, MutationError, PageHeader, StatusBadge } from "./components";
import type { Agent, FinancialAction, Fleet, Organization } from "./types";

const newIdempotencyKey = (): string =>
  globalThis.crypto?.randomUUID?.() ??
  `operator-${Date.now()}-${Math.random().toString(16).slice(2)}`;

export function FinancialActionsPage() {
  const queryClient = useQueryClient();
  const organizations = useQuery({
    queryKey: ["organizations"],
    queryFn: () => apiRequest<Organization[]>("organizations?limit=500"),
  });
  const fleets = useQuery({
    queryKey: ["fleets"],
    queryFn: () => apiRequest<Fleet[]>("fleets?limit=500"),
  });
  const agents = useQuery({
    queryKey: ["agents"],
    queryFn: () => apiRequest<Agent[]>("agents?limit=500"),
  });
  const actions = useQuery({
    queryKey: ["financial-actions"],
    queryFn: () => apiRequest<FinancialAction[]>("financial-actions?limit=500"),
  });
  const [draft, setDraft] = useState({
    organizationId: "",
    fleetId: "",
    agentId: "",
    actionType: "payment",
    resource: "accounts/operating",
    amount: "",
    currency: "USD",
    idempotencyKey: newIdempotencyKey(),
    metadata: "{}",
  });
  const [validationError, setValidationError] = useState("");
  const [decision, setDecision] = useState<FinancialAction | null>(null);
  const [reversal, setReversal] = useState<FinancialAction | null>(null);
  const execute = useMutation({
    mutationFn: (context: Record<string, unknown>) =>
      apiRequest<FinancialAction>("financial-actions", {
        method: "POST",
        body: JSON.stringify({
          agent_id: draft.agentId,
          idempotency_key: draft.idempotencyKey.trim(),
          action_type: draft.actionType,
          resource: draft.resource.trim(),
          amount: draft.amount,
          currency: draft.currency.trim().toUpperCase(),
          context,
        }),
      }),
    onSuccess: (result) => {
      setDecision(result);
      setDraft((current) => ({
        ...current,
        amount: "",
        idempotencyKey: newIdempotencyKey(),
      }));
      queryClient.invalidateQueries({ queryKey: ["financial-actions"] });
      queryClient.invalidateQueries({ queryKey: ["overview"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const reverse = useMutation({
    mutationFn: (action: FinancialAction) =>
      apiRequest<FinancialAction>(`financial-actions/${action.id}/reverse`, {
        method: "POST",
        body: JSON.stringify({ reason: "Operator-requested reversal" }),
      }),
    onSuccess: (result) => {
      setReversal(result);
      setDecision(result);
      queryClient.invalidateQueries({ queryKey: ["financial-actions"] });
      queryClient.invalidateQueries({ queryKey: ["overview"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
    },
  });
  const availableFleets = useMemo(
    () =>
      (fleets.data ?? []).filter(
        (fleet) => !draft.organizationId || fleet.organization_id === draft.organizationId,
      ),
    [draft.organizationId, fleets.data],
  );
  const availableAgents = useMemo(
    () => (agents.data ?? []).filter((agent) => !draft.fleetId || agent.fleet_id === draft.fleetId),
    [agents.data, draft.fleetId],
  );
  const settledActions = (actions.data ?? []).filter((action) => action.status === "settled");
  const loading = organizations.isLoading || fleets.isLoading || agents.isLoading;

  const submit = () => {
    setValidationError("");
    if (!draft.organizationId || !draft.fleetId || !draft.agentId) {
      setValidationError("Choose an organization, fleet, and agent.");
      return;
    }
    if (!draft.resource.trim() || !draft.idempotencyKey.trim()) {
      setValidationError("Resource and idempotency key are required.");
      return;
    }
    if (!(Number(draft.amount) > 0) || !/^[A-Z]{3}$/.test(draft.currency.toUpperCase())) {
      setValidationError("Enter a positive amount and a three-letter currency code.");
      return;
    }
    try {
      const context = JSON.parse(draft.metadata) as unknown;
      if (!context || Array.isArray(context) || typeof context !== "object") {
        setValidationError("Request metadata must be a JSON object.");
        return;
      }
      execute.mutate(context as Record<string, unknown>);
    } catch {
      setValidationError("Request metadata must contain valid JSON.");
    }
  };

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Governed execution"
        title="Financial actions"
        description="Submit payments, transfers, and refunds only through the Financial Governance Gateway."
      />
      <form
        className="policy-form panel"
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <label>
          Organization
          <select
            required
            value={draft.organizationId}
            onChange={(event) =>
              setDraft({
                ...draft,
                organizationId: event.target.value,
                fleetId: "",
                agentId: "",
              })
            }
          >
            <option value="">Select organization</option>
            {organizations.data?.map((organization) => (
              <option key={organization.id} value={organization.id}>
                {organization.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Fleet
          <select
            required
            value={draft.fleetId}
            onChange={(event) => setDraft({ ...draft, fleetId: event.target.value, agentId: "" })}
          >
            <option value="">Select fleet</option>
            {availableFleets.map((fleet) => (
              <option key={fleet.id} value={fleet.id}>
                {fleet.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Agent
          <select
            required
            value={draft.agentId}
            onChange={(event) => setDraft({ ...draft, agentId: event.target.value })}
          >
            <option value="">Select agent</option>
            {availableAgents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Action
          <select
            value={draft.actionType}
            onChange={(event) => setDraft({ ...draft, actionType: event.target.value })}
          >
            <option value="payment">Payment</option>
            <option value="transfer">Transfer</option>
            <option value="refund">Refund</option>
          </select>
        </label>
        <label>
          Resource
          <input
            required
            value={draft.resource}
            onChange={(event) => setDraft({ ...draft, resource: event.target.value })}
          />
        </label>
        <label>
          Amount
          <input
            required
            min="0.01"
            step="0.01"
            type="number"
            value={draft.amount}
            onChange={(event) => setDraft({ ...draft, amount: event.target.value })}
          />
        </label>
        <label>
          Currency
          <input
            required
            maxLength={3}
            value={draft.currency}
            onChange={(event) => setDraft({ ...draft, currency: event.target.value.toUpperCase() })}
          />
        </label>
        <label>
          Idempotency key
          <input
            required
            value={draft.idempotencyKey}
            onChange={(event) => setDraft({ ...draft, idempotencyKey: event.target.value })}
          />
        </label>
        <label>
          Request metadata JSON
          <textarea
            rows={3}
            value={draft.metadata}
            onChange={(event) => setDraft({ ...draft, metadata: event.target.value })}
          />
        </label>
        <button className="primary-button" disabled={loading || execute.isPending}>
          <Send size={16} /> Submit governed action
        </button>
      </form>
      {validationError && (
        <div className="form-alert" role="alert">
          {validationError}
        </div>
      )}
      <MutationError error={execute.error ?? reverse.error ?? null} />
      {decision && <DecisionResult decision={decision} reversal={reversal} />}
      <section className="panel operator-panel">
        <div className="panel-header">
          <div>
            <span className="section-label">Compensating control</span>
            <h2>Settled transactions</h2>
          </div>
        </div>
        <DataState loading={actions.isLoading} error={actions.error} empty={!settledActions.length}>
          <div className="record-list">
            {settledActions.map((action) => (
              <article key={action.id}>
                <div>
                  <strong>
                    {action.action_type} · {action.amount} {action.currency}
                  </strong>
                  <span>
                    {action.id} · {new Date(action.timestamp).toLocaleString()}
                  </span>
                </div>
                <ConfirmButton
                  message={`Reverse ${action.amount} ${action.currency} transaction ${action.id}?`}
                  onConfirm={() => reverse.mutate(action)}
                >
                  <RotateCcw size={14} /> Reverse
                </ConfirmButton>
              </article>
            ))}
          </div>
        </DataState>
      </section>
    </div>
  );
}

function DecisionResult({
  decision,
  reversal,
}: {
  decision: FinancialAction;
  reversal: FinancialAction | null;
}) {
  const rejectionType = !decision.permission_allowed
    ? "Permission rejection"
    : !decision.spend_allowed
      ? "Budget or emergency rejection"
      : "Gateway rejection";
  return (
    <section className="panel decision-panel" aria-live="polite">
      <div className="panel-header">
        <div>
          <span className="section-label">
            {decision.allowed ? "Approved" : decision.status === "reversed" ? "Reversed" : "Denied"}
          </span>
          <h2>Governance decision</h2>
        </div>
        <StatusBadge value={decision.status} />
      </div>
      {!decision.allowed && decision.status !== "reversed" && (
        <div className="form-alert" role="status">
          <strong>{rejectionType}:</strong> {decision.reason}
        </div>
      )}
      <dl>
        <div>
          <dt>Execution ID</dt>
          <dd>{decision.id}</dd>
        </div>
        <div>
          <dt>Audit reference</dt>
          <dd>{decision.request_id}</dd>
        </div>
        <div>
          <dt>Policy</dt>
          <dd>{decision.policy_id ?? "No matching policy"}</dd>
        </div>
        <div>
          <dt>Adapter reference</dt>
          <dd>{decision.adapter_reference ?? "Not executed"}</dd>
        </div>
        {reversal && (
          <>
            <div>
              <dt>Transaction ID</dt>
              <dd>{reversal.id}</dd>
            </div>
            <div>
              <dt>Reversal status</dt>
              <dd>{reversal.status}</dd>
            </div>
            <div>
              <dt>Reversal audit entry</dt>
              <dd>{reversal.request_id}</dd>
            </div>
          </>
        )}
      </dl>
      <Link className="secondary-button" to="/audit">
        <ArrowLeftRight size={15} /> Open Audit Center
      </Link>
    </section>
  );
}
