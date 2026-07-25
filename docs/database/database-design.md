# Database design

| Table | Responsibility |
| --- | --- |
| `users` | Persistent username, role, password hash, enabled state, token version |
| `auth_sessions` | Hashed rotating refresh token, expiry, revocation, rotation time |
| `organizations` | Top-level governance scope and status |
| `fleets` | Organization-owned agent grouping and emergency status |
| `agents` | Financial agent identity, owner, fleet, type, operational status |
| `policies` | Effect, action/resource match, conditions, priority, uncapped authorization |
| `permissions` | Unique agent-to-policy assignment |
| `spend_limits` | Agent transaction/daily/monthly currency limit |
| `fleet_spend_limits` | Fleet-scoped equivalent |
| `organization_spend_limits` | Organization-scoped equivalent |
| `financial_actions` | Idempotent request, decisions, execution outcome, adapter reference |
| `budget_reservations` | Reserved amount and settlement/release/reversal state |
| `spend_records` | Append-only settlement and reversal ledger |
| `audit_logs` | Append-only actor, scope, decision, tracing, and execution evidence |

Money uses `NUMERIC(18,2)`. Currency values are validated as three uppercase letters. Application
timestamps are UTC and server-owned for governed execution. Unique constraints prevent duplicate
assignments, duplicate limits per scope/period/currency, duplicate request IDs, and reuse of an
idempotency key for the same agent.

There is no `RiskEvents` table. Assessment Lab results are intentionally browser-local.
