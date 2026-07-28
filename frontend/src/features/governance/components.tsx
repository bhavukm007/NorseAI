import { useEffect, useId, useRef, useState, type ReactNode } from "react";

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
  const [open, setOpen] = useState(false);

  return (
    <>
      <button className={className} type="button" onClick={() => setOpen(true)}>
        {children}
      </button>
      <Modal open={open} title="Confirm action" onClose={() => setOpen(false)}>
        <p>{message}</p>
        <div className="modal-actions">
          <button type="button" onClick={() => setOpen(false)}>
            Cancel
          </button>
          <button
            className={className}
            type="button"
            onClick={() => {
              setOpen(false);
              onConfirm();
            }}
          >
            Confirm
          </button>
        </div>
      </Modal>
    </>
  );
}

export function Modal({
  open,
  title,
  onClose,
  children,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const titleId = useId();
  const dialog = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
      previous?.focus();
    };
  }, [onClose, open]);

  if (!open) return null;
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        aria-labelledby={titleId}
        aria-modal="true"
        className="modal-card"
        ref={dialog}
        role="dialog"
        tabIndex={-1}
      >
        <div className="modal-header">
          <h2 id={titleId}>{title}</h2>
          <button aria-label="Close dialog" type="button" onClick={onClose}>
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function MutationError({ error }: { error: Error | null }) {
  if (!error) return null;
  return (
    <div className="form-alert" role="alert">
      {error.message}
    </div>
  );
}
