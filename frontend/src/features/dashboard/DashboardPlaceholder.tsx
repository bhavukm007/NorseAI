export function DashboardPlaceholder() {
  return (
    <section className="page" aria-labelledby="page-title">
      <p className="eyebrow">Platform foundation</p>
      <h1 id="page-title">NorseAI workspace</h1>
      <p className="page-description">
        The application shell is ready. Governance capabilities and operational dashboards will be
        introduced in their scheduled phases.
      </p>
      <div className="foundation-card">
        <span className="status-dot" aria-hidden="true" />
        <div>
          <strong>Foundation configured</strong>
          <p>API, routing, environment configuration, and infrastructure are available.</p>
        </div>
      </div>
    </section>
  );
}
