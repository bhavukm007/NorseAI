import { useQuery } from "@tanstack/react-query";
import { Bot, Building2, CircleDollarSign, Radio, ShieldAlert, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { StatusCard } from "../../components/dashboard/StatusCard";
import { useSystemHealth } from "../../hooks/useSystemHealth";
import { apiRequest } from "../../lib/api/client";
import { DataState, PageHeader, StatusBadge } from "../governance/components";
import type { Overview } from "../governance/types";

export function DashboardPage() {
  const health = useSystemHealth();
  const overview = useQuery({
    queryKey: ["overview"],
    queryFn: () => apiRequest<Overview>("overview"),
    refetchInterval: 15_000,
  });
  const data = overview.data;
  const utilization =
    data && Number(data.budget_limit)
      ? Math.round((Number(data.settled_spend) / Number(data.budget_limit)) * 100)
      : 0;

  return (
    <div className="dashboard-page">
      <PageHeader
        eyebrow="Financial agent governance"
        title="Operator control center"
        description="Live enforcement, budgets, emergency state, and immutable decisions."
        actions={
          <Link className="secondary-button" to="/assessment-lab">
            <Bot size={16} /> AI Assessment Lab
          </Link>
        }
      />
      <section className="status-grid operator-status-grid" aria-label="Governance status">
        <StatusCard
          icon={Radio}
          title="System health"
          value={health.health.connected ? "Connected" : "Offline"}
          detail={
            health.health.latency
              ? `${health.health.latency} ms API latency`
              : "FastAPI governance service"
          }
          tone={health.health.connected ? "positive" : "warning"}
          loading={health.loading}
        />
        <StatusCard
          icon={ShieldCheck}
          title="Active agents"
          value={String(data?.active_agents ?? "—")}
          detail="Enabled financial agents"
          tone="positive"
          loading={overview.isLoading}
        />
        <StatusCard
          icon={Building2}
          title="Active fleets"
          value={String(data?.active_fleets ?? "—")}
          detail="Fleets accepting governed actions"
          tone="accent"
          loading={overview.isLoading}
        />
        <StatusCard
          icon={CircleDollarSign}
          title="Budget utilization"
          value={`${utilization}%`}
          detail={
            data
              ? `${data.settled_spend} settled of ${data.budget_limit} USD limits`
              : "Loading budget ledger"
          }
          tone={utilization > 80 ? "warning" : "positive"}
          loading={overview.isLoading}
        />
        <StatusCard
          icon={ShieldAlert}
          title="Emergency fleets"
          value={String(data?.emergency_fleets ?? "—")}
          detail="Fleet-wide execution stops"
          tone={data?.emergency_fleets ? "warning" : "positive"}
          loading={overview.isLoading}
        />
      </section>
      <DataState loading={overview.isLoading} error={overview.error} empty={!data}>
        <div className="operator-grid two-column">
          <section className="panel operator-panel">
            <div className="panel-header">
              <div>
                <span className="section-label">Enforcement</span>
                <h2>Recent decisions</h2>
              </div>
              <Link to="/audit">View audit</Link>
            </div>
            <div className="record-list">
              {data?.recent_decisions.map((item) => (
                <article key={item.id}>
                  <div>
                    <strong>{item.action_type}</strong>
                    <span>
                      {item.amount} {item.currency} · {item.reason}
                    </span>
                  </div>
                  <StatusBadge value={item.status} />
                </article>
              ))}
              {!data?.recent_decisions.length && (
                <div className="data-state">No governed actions yet.</div>
              )}
            </div>
          </section>
          <section className="panel operator-panel">
            <div className="panel-header">
              <div>
                <span className="section-label">Immutable trail</span>
                <h2>Recent audit events</h2>
              </div>
            </div>
            <div className="record-list">
              {data?.recent_audits.map((item) => (
                <article key={item.id}>
                  <div>
                    <strong>{item.action}</strong>
                    <span>
                      {item.username} · {new Date(item.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <StatusBadge value={item.result} />
                </article>
              ))}
              {!data?.recent_audits.length && (
                <div className="data-state">No audit events yet.</div>
              )}
            </div>
          </section>
        </div>
      </DataState>
    </div>
  );
}
