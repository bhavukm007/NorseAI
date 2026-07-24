import { useCallback, useEffect, useRef, useState } from "react";

import { apiRequest } from "../lib/api/client";

interface HealthResponse {
  status: "healthy";
  service: string;
  version: string;
}

export interface SystemHealth {
  connected: boolean;
  latency: number | null;
  lastSync: Date | null;
  service: string;
  version: string;
}

const initialHealth: SystemHealth = {
  connected: false,
  latency: null,
  lastSync: null,
  service: "NorseAI API",
  version: "—",
};

export function useSystemHealth() {
  const [health, setHealth] = useState(initialHealth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mounted = useRef(true);
  const initialLoad = useRef(true);

  const refresh = useCallback(async () => {
    if (initialLoad.current) setLoading(true);
    const started = performance.now();
    try {
      const result = await apiRequest<HealthResponse>("health");
      if (!mounted.current) return;
      setHealth({
        connected: result.status === "healthy",
        latency: Math.round(performance.now() - started),
        lastSync: new Date(),
        service: result.service,
        version: result.version,
      });
      setError(null);
    } catch {
      if (!mounted.current) return;
      setHealth((current) => ({
        ...current,
        connected: false,
        latency: null,
        lastSync: new Date(),
      }));
      setError("Unable to reach the backend.");
    } finally {
      initialLoad.current = false;
      if (mounted.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    void refresh();
    const interval = window.setInterval(refresh, 30_000);
    window.addEventListener("norse:refresh", refresh);
    return () => {
      mounted.current = false;
      window.clearInterval(interval);
      window.removeEventListener("norse:refresh", refresh);
    };
  }, [refresh]);

  return { health, loading, error, refresh };
}
