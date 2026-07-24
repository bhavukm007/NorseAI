import { createContext, useContext } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastInput {
  title: string;
  message?: string;
  type?: ToastType;
}

export interface Toast extends ToastInput {
  id: string;
  type: ToastType;
}

export interface ToastContextValue {
  notify: (toast: ToastInput) => string;
  dismiss: (id: string) => void;
}

export const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const value = useContext(ToastContext);
  if (!value) throw new Error("useToast must be used within ToastProvider.");
  return value;
}
