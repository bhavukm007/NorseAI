import { ArrowLeft, Construction } from "lucide-react";
import { Link } from "react-router-dom";

export function FeaturePage({ feature }: { feature: string }) {
  return (
    <section className="feature-page">
      <span className="feature-icon">
        <Construction size={24} />
      </span>
      <span className="eyebrow">Workspace module</span>
      <h1>{feature}</h1>
      <p>
        {feature} has a reserved route in the Phase 03 application shell. Its full workflow will be
        connected in the scheduled product phase.
      </p>
      <Link className="secondary-button" to="/dashboard">
        <ArrowLeft size={16} /> Back to dashboard
      </Link>
    </section>
  );
}
