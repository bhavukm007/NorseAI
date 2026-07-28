import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiRequest, loadSession, saveSession } from "../../lib/api/client";
import { AuthContext } from "./auth";

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_at: string;
  username: string;
  role: string;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState(loadSession);

  const logout = useCallback(async () => {
    try {
      await apiRequest<void>("auth/logout", {
        method: "POST",
        body: JSON.stringify({}),
      });
    } finally {
      saveSession(null);
      setSession(null);
    }
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const result = await apiRequest<LoginResponse>("auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    const next = {
      accessToken: result.access_token,
      refreshToken: result.refresh_token,
      expiresAt: result.expires_at,
      username: result.username,
      role: result.role,
    };
    saveSession(next);
    setSession(next);
  }, []);

  useEffect(() => {
    const sync = () => setSession(loadSession());
    window.addEventListener("norse:session", sync);
    const interval = window.setInterval(sync, 30_000);
    return () => {
      window.removeEventListener("norse:session", sync);
      window.clearInterval(interval);
    };
  }, []);

  const value = useMemo(() => ({ session, login, logout }), [login, logout, session]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
