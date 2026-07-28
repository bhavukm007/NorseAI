import { useQuery } from "@tanstack/react-query";
import { Download, Search } from "lucide-react";
import { useState } from "react";

import { apiRequest, downloadAudit } from "../../lib/api/client";
import { DataState, MutationError, PageHeader, StatusBadge } from "./components";
import type { AuditLog } from "./types";

export function AuditPage() {
  const [exportError, setExportError] = useState<Error | null>(null);
  const [exporting, setExporting] = useState<"csv" | "jsonl" | null>(null);
  const [filters, setFilters] = useState({
    search: "",
    actor: "",
    fleet: "",
    organization: "",
    policy: "",
    action: "",
    result: "",
    date_from: "",
    date_to: "",
    offset: 0,
  });
  const query = new URLSearchParams(
    Object.entries(filters)
      .filter(([, value]) => value !== "" && value !== 0)
      .map(([key, value]) => [
        { fleet: "fleet_id", organization: "organization_id", policy: "policy_id" }[key] ?? key,
        String(value),
      ]),
  );
  query.set("limit", "25");
  const audits = useQuery({
    queryKey: ["audit", filters],
    queryFn: () => apiRequest<AuditLog[]>(`audit-logs?${query}`),
  });
  const update = (key: string, value: string | number) =>
    setFilters((current) => ({
      ...current,
      [key]: value,
      offset: key === "offset" ? Number(value) : 0,
    }));
  const exportAudit = async (format: "csv" | "jsonl") => {
    setExportError(null);
    setExporting(format);
    try {
      await downloadAudit(format);
    } catch (error) {
      setExportError(error instanceof Error ? error : new Error("Audit export failed."));
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="operator-page">
      <PageHeader
        eyebrow="Immutable evidence"
        title="Audit center"
        description="Search, filter, inspect, and export every governance decision."
        actions={
          <>
            <button disabled={exporting !== null} onClick={() => void exportAudit("csv")}>
              <Download size={15} /> {exporting === "csv" ? "Exporting…" : "CSV"}
            </button>
            <button disabled={exporting !== null} onClick={() => void exportAudit("jsonl")}>
              <Download size={15} /> {exporting === "jsonl" ? "Exporting…" : "JSONL"}
            </button>
          </>
        }
      />
      <MutationError error={exportError} />
      <div className="audit-filters panel">
        <label className="search-field">
          <Search size={15} />
          <input
            aria-label="Search audit events"
            placeholder="Search actor, action, resource, result"
            value={filters.search}
            onChange={(e) => update("search", e.target.value)}
          />
        </label>
        <input
          aria-label="Filter actor"
          placeholder="Actor"
          value={filters.actor}
          onChange={(e) => update("actor", e.target.value)}
        />
        <input
          aria-label="Filter fleet"
          placeholder="Fleet ID"
          value={filters.fleet}
          onChange={(e) => update("fleet", e.target.value)}
        />
        <input
          aria-label="Filter organization"
          placeholder="Organization ID"
          value={filters.organization}
          onChange={(e) => update("organization", e.target.value)}
        />
        <input
          aria-label="Filter policy"
          placeholder="Policy reference"
          value={filters.policy}
          onChange={(e) => update("policy", e.target.value)}
        />
        <input
          aria-label="Filter action"
          placeholder="Action"
          value={filters.action}
          onChange={(e) => update("action", e.target.value)}
        />
        <select
          aria-label="Filter result"
          value={filters.result}
          onChange={(e) => update("result", e.target.value)}
        >
          <option value="">All results</option>
          <option value="success">Success</option>
          <option value="allowed">Allowed</option>
          <option value="denied">Denied</option>
          <option value="settled">Settled</option>
          <option value="rejected">Rejected</option>
        </select>
        <input
          aria-label="From date"
          type="datetime-local"
          value={filters.date_from}
          onChange={(e) => update("date_from", e.target.value)}
        />
        <input
          aria-label="To date"
          type="datetime-local"
          value={filters.date_to}
          onChange={(e) => update("date_to", e.target.value)}
        />
      </div>
      <DataState loading={audits.isLoading} error={audits.error} empty={!audits.data?.length}>
        <div className="audit-list">
          {audits.data?.map((item) => (
            <details className="audit-event panel" key={item.id}>
              <summary>
                <div>
                  <strong>{item.action}</strong>
                  <span>
                    {item.username} · {new Date(item.timestamp).toLocaleString()}
                  </span>
                </div>
                <StatusBadge value={item.result} />
              </summary>
              <dl>
                <div>
                  <dt>Request</dt>
                  <dd>{item.request_id ?? "—"}</dd>
                </div>
                <div>
                  <dt>Agent</dt>
                  <dd>{item.agent_reference ?? "—"}</dd>
                </div>
                <div>
                  <dt>Fleet</dt>
                  <dd>{item.fleet_id ?? "—"}</dd>
                </div>
                <div>
                  <dt>Organization</dt>
                  <dd>{item.organization_id ?? "—"}</dd>
                </div>
                <div>
                  <dt>Policy</dt>
                  <dd>{item.policy_reference ?? "—"}</dd>
                </div>
                <div>
                  <dt>Policy decision</dt>
                  <dd>{item.policy_decision ?? "—"}</dd>
                </div>
                <div>
                  <dt>Spend decision</dt>
                  <dd>{item.spend_decision ?? "—"}</dd>
                </div>
                <div>
                  <dt>Execution</dt>
                  <dd>{item.execution_result ?? "—"}</dd>
                </div>
                <div>
                  <dt>Amount</dt>
                  <dd>{item.amount ? `${item.amount} ${item.currency}` : "—"}</dd>
                </div>
                <div>
                  <dt>Resource</dt>
                  <dd>{item.resource}</dd>
                </div>
              </dl>
            </details>
          ))}
        </div>
      </DataState>
      <div className="pagination">
        <button
          disabled={!filters.offset}
          onClick={() => update("offset", Math.max(0, filters.offset - 25))}
        >
          Previous
        </button>
        <span>Page {Math.floor(filters.offset / 25) + 1}</span>
        <button
          disabled={(audits.data?.length ?? 0) < 25}
          onClick={() => update("offset", filters.offset + 25)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
