import { CheckCircle2, CircleAlert, Info, TriangleAlert, X } from "lucide-react";
import { type PropsWithChildren, useCallback, useMemo, useState } from "react";

import { ToastContext, type Toast, type ToastInput } from "./toast";

const toastIcons = {
  success: CheckCircle2,
  error: CircleAlert,
  warning: TriangleAlert,
  info: Info,
};

export function ToastProvider({ children }: PropsWithChildren) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((items) => items.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback(
    (input: ToastInput) => {
      const id = crypto.randomUUID();
      setToasts((items) => [...items, { ...input, id, type: input.type ?? "info" }]);
      window.setTimeout(() => dismiss(id), 4500);
      return id;
    },
    [dismiss],
  );

  const value = useMemo(() => ({ notify, dismiss }), [dismiss, notify]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-region" aria-live="polite" aria-label="Notifications" role="region">
        {toasts.map((toast) => {
          const Icon = toastIcons[toast.type];
          return (
            <div className={`toast toast-${toast.type}`} key={toast.id} role="status">
              <Icon size={19} />
              <div>
                <strong>{toast.title}</strong>
                {toast.message && <span>{toast.message}</span>}
              </div>
              <button onClick={() => dismiss(toast.id)} aria-label="Dismiss notification">
                <X size={16} />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
