import type { LucideIcon } from "lucide-react";

export interface StatusCardProps {
  icon: LucideIcon;
  title: string;
  value: string;
  detail: string;
  tone?: "positive" | "warning" | "neutral" | "accent";
  loading?: boolean;
  unavailable?: boolean;
}

export function StatusCard({
  icon: Icon,
  title,
  value,
  detail,
  tone = "neutral",
  loading,
  unavailable,
}: StatusCardProps) {
  if (loading) {
    return (
      <article className="metric-card skeleton-card" aria-label={`${title} loading`}>
        <span className="skeleton skeleton-square" />
        <span className="skeleton skeleton-line short" />
        <span className="skeleton skeleton-value" />
        <span className="skeleton skeleton-line" />
      </article>
    );
  }

  return (
    <article className={`metric-card tone-${tone} ${unavailable ? "is-unavailable" : ""}`}>
      <div className="metric-card-top">
        <span className="metric-icon">
          <Icon size={19} />
        </span>
      </div>
      <span className="metric-title">{title}</span>
      <strong className="metric-value">{value}</strong>
      <span className="metric-detail">{detail}</span>
      {unavailable && <span className="placeholder-badge">Not connected</span>}
    </article>
  );
}
