import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="operator-page-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </header>
  );
}

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`status-badge status-${value.replaceAll("_", "-")}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function DataState({
  loading,
  error,
  empty,
  children,
}: {
  loading: boolean;
  error: Error | null;
  empty: boolean;
  children: ReactNode;
}) {
  if (loading)
    return (
      <div className="data-state" role="status">
        Loading live governance data…
      </div>
    );
  if (error)
    return (
      <div className="data-state error" role="alert">
        {error.message}
      </div>
    );
  if (empty) return <div className="data-state">No records match this view.</div>;
  return <>{children}</>;
}

export function ConfirmButton({
  children,
  message,
  onConfirm,
  className = "",
}: {
  children: ReactNode;
  message: string;
  onConfirm: () => void;
  className?: string;
}) {
  return (
    <button className={className} onClick={() => window.confirm(message) && onConfirm()}>
      {children}
    </button>
  );
}
