# NorseAI project specification

## Product definition

NorseAI is an authenticated operator platform that governs autonomous financial agents. It
combines deterministic policy decisions, hierarchical spend controls, fleet-wide emergency
control, sandbox execution, and immutable evidence in one traceable workflow. The AI Assessment
Lab is a complementary demonstration surface, not the operational enforcement boundary.

## Implemented scope

### Identity and authorization

- Persistent users with Admin, Operator, Auditor, and Viewer roles.
- Scrypt password hashes and environment-backed bootstrap operator credentials.
- Signed issuer- and audience-scoped JWT access tokens.
- Rotating, hashed refresh sessions with expiry and logout revocation.
- Persistent-user, role, token-version, and session validation on every protected request.
- Admin user enable/disable operations that invalidate active sessions.

### Governance

- Organizations, fleets, and agents with explicit operational status.
- Allow, deny, and conditional policies assigned to agents.
- Deterministic precedence: priority, deny/conditional/allow effect, creation time, then UUID.
- Default denial when no applicable policy authorizes an action.
- Agent, fleet, and organization transaction/daily/monthly spend limits.
- Explicit policy authorization for intentionally uncapped execution.

### Financial execution

- Payments, transfers, and refunds through a mandatory server-side gateway.
- Server-owned timestamps and per-agent idempotency keys.
- Budget reservation before adapter invocation.
- Settlement, rejection, release, and compensating reversal records.
- Sandbox adapter only; no external financial network is connected.

### Evidence and operations

- Append-only audit records and immutable spend records.
- Request IDs, correlation IDs, structured metadata, decision context, and policy versions.
- CSV and JSONL audit export.
- Operator pages for overview, agents, fleets, policies, budgets, emergency control, and audit.
- Deterministic AI Assessment Lab with browser-local history and PDF/JSON/CSV report export.

## Quality attributes

- Python 3.11+ and Node.js 20+.
- PostgreSQL production persistence and Alembic migration history.
- Validated environment settings with production secret requirements.
- RBAC, rate limits, CORS controls, security headers, stable error envelopes, and bounded inputs.
- Non-root backend container and static Nginx frontend container.
- Backend/frontend tests, linting, formatting, dependency scanning, migration checks, container
  builds, and PostgreSQL integration in CI.

## Deliberate boundaries

- Redis and OPA are provisioned but not used by the current decision path.
- Rate limiting is process-local and should be replaced by a shared store for horizontal scaling.
- The financial adapter is a deterministic sandbox, not a banking integration.
- Assessment history is browser-local and separate from operational governance persistence.
- No monitoring stack, background worker, notification service, or conversational AI endpoint is
  claimed.

## Acceptance criteria

A release is acceptable when migrations have one head, backend and frontend validation pass,
production builds succeed, Compose validates with explicit secrets, protected endpoints reject
invalid or revoked sessions, financial actions cannot bypass governance, and audit exports retain
decision evidence.
