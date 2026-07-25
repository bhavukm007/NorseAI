import { createContext, useContext } from "react";

import type { StoredSession } from "../../lib/api/client";

export interface AuthContextValue {
  session: StoredSession | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
