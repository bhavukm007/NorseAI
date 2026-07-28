import { LockKeyhole } from "lucide-react";
import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { BrandMark } from "../../components/brand/BrandMark";
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
        <div className="login-brand">
          <BrandMark />
          <div>
            <strong>NorseAI</strong>
            <span>Governance intelligence</span>
          </div>
        </div>
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
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete="current-password"
          />
        </label>
        <button className="primary-button" disabled={busy}>
          {busy ? "Signing in…" : "Sign in securely"}
        </button>
        <span className="login-security-note">
          <LockKeyhole size={13} aria-hidden="true" /> Protected operator session
        </span>
      </form>
    </main>
  );
}
