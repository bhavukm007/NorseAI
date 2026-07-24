import { BarChart3 } from "lucide-react";

export function SystemMetrics() {
  return (
    <section className="panel metrics-panel" aria-labelledby="metrics-title">
      <div className="panel-header">
        <div>
          <span className="section-label">Metrics source unavailable</span>
          <h2 id="metrics-title">System metrics</h2>
        </div>
      </div>
      <div className="empty-state" role="status">
        <span className="empty-icon">
          <BarChart3 size={20} aria-hidden="true" />
        </span>
        <strong>No live metrics yet</strong>
        <p>
          Aggregates will appear when a metrics endpoint and authenticated session are available.
        </p>
      </div>
    </section>
  );
}
