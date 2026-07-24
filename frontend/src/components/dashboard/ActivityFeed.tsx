import { Clock3 } from "lucide-react";

export function ActivityFeed() {
  return (
    <section className="panel activity-panel" aria-labelledby="activity-title">
      <div className="panel-header">
        <div>
          <span className="section-label">Activity source unavailable</span>
          <h2 id="activity-title">Recent activity</h2>
        </div>
      </div>
      <div className="empty-state" role="status">
        <span className="empty-icon">
          <Clock3 size={20} aria-hidden="true" />
        </span>
        <strong>No live activity data</strong>
        <p>Events will appear here after an authenticated activity API is connected.</p>
      </div>
    </section>
  );
}
