import { ArrowLeft, Construction } from "lucide-react";
import { Link } from "react-router-dom";

export function FeaturePage({ feature }: { feature: string }) {
  const descriptions: Record<string, string> = {
    Chat: "The assistant channel is reserved for a future secured AI service connection.",
    Governance:
      "Policy administration remains protected by the authenticated governance API. Use the simulator for the public assessment workflow.",
    Analytics:
      "Portfolio analytics will activate when authenticated assessment telemetry is connected.",
    History:
      "Assessment history is available inside the simulator and remains private to this browser.",
    Settings:
      "Workspace configuration is managed through environment variables and the theme control in the header.",
  };

  return (
    <section className="feature-page">
      <span className="feature-icon">
        <Construction size={24} />
      </span>
      <span className="eyebrow">Workspace module</span>
      <h1>{feature}</h1>
      <p>
        {descriptions[feature] ??
          "This workspace module is ready for a future authenticated service connection."}
      </p>
      <div className="feature-actions">
        <Link className="secondary-button" to="/dashboard">
          <ArrowLeft size={16} /> Back to dashboard
        </Link>
        {feature !== "Chat" && (
          <Link className="primary-button" to="/simulator">
            Open simulator
          </Link>
        )}
      </div>
    </section>
  );
}
