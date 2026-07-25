import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "./auth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  return (
    <main className="login-page">
      <form
        className="login-card"
        onSubmit={async (event) => {
          event.preventDefault();
          setBusy(true);
          setError("");
          try {
            await login(username, password);
            const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";
            navigate(from, { replace: true });
          } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Login failed");
          } finally {
            setBusy(false);
          }
        }}
      >
        <span className="login-mark">
          <ShieldCheck size={28} />
        </span>
        <span className="eyebrow">Operator access</span>
        <h1>Govern financial agents</h1>
        <p>Sign in to manage fleets, policies, budgets, emergency controls, and audit evidence.</p>
        {error && (
          <div className="form-alert" role="alert">
            {error}
          </div>
        )}
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>
        <button className="primary-button" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}
