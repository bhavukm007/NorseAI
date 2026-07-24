import { Bot, BrainCircuit, Play, Radio, RefreshCw, ScrollText, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

import { ChatPanel } from "../../components/chat/ChatPanel";
import { ActivityFeed } from "../../components/dashboard/ActivityFeed";
import { StatusCard } from "../../components/dashboard/StatusCard";
import { SystemMetrics } from "../../components/dashboard/SystemMetrics";
import { useSystemHealth } from "../../hooks/useSystemHealth";

function formatSync(date: Date | null) {
  if (!date) return "Waiting for first sync";
  return `Synced ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

export function DashboardPage() {
  const { health, loading, error, refresh } = useSystemHealth();

  return (
    <div className="dashboard-page">
      <section className="dashboard-intro">
        <div>
          <span className="eyebrow">Operations overview</span>
          <h1>Operations overview</h1>
          <p>Live status is shown only where a backend data source is available.</p>
        </div>
        <Link className="demo-launch-button" to="/simulator?demo=1">
          <span>
            <Play size={15} fill="currentColor" />
          </span>
          <div>
            <strong>Run judge demo</strong>
            <small>Complete governance flow</small>
          </div>
        </Link>
      </section>

      {error && (
        <div className="inline-alert" role="alert">
          <div>
            <strong>Backend connection unavailable</strong>
            <span>{error} Dashboard preview data remains available.</span>
          </div>
          <button onClick={() => void refresh()}>
            <RefreshCw size={15} /> Retry
          </button>
        </div>
      )}

      <section className="status-grid" aria-label="System status">
        <StatusCard
          icon={Radio}
          title="Backend status"
          value={health.connected ? "Connected" : error ? "Offline" : "Checking"}
          detail={
            health.latency !== null
              ? `${health.latency} ms latency · v${health.version}`
              : formatSync(health.lastSync)
          }
          tone={health.connected ? "positive" : "warning"}
          loading={loading}
        />
        <StatusCard
          icon={ShieldCheck}
          title="Governance status"
          value="—"
          detail="Requires an authenticated governance status endpoint"
          unavailable
        />
        <StatusCard
          icon={Bot}
          title="Simulator status"
          value="Ready"
          detail="Interactive governance assessments available"
          tone="positive"
        />
        <StatusCard
          icon={ScrollText}
          title="Active policies"
          value="—"
          detail="Requires an authenticated policy summary endpoint"
          unavailable
        />
        <StatusCard
          icon={BrainCircuit}
          title="AI health"
          value="—"
          detail="AI service health is not exposed by the backend"
          unavailable
        />
      </section>

      <div className="dashboard-columns">
        <div className="primary-column">
          <SystemMetrics />
          <ActivityFeed />
        </div>
        <ChatPanel />
      </div>
    </div>
  );
}
