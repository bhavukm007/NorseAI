# Phase 06: Financial Governance Core

## Delivered

- Persistent organizations and fleets with enabled, disabled, and emergency-stopped fleet states.
- Mandatory governed execution for sandbox payments, transfers, and refunds.
- Existing agent permission policies enforced inside the execution path.
- Agent, fleet, and organization budget checks using authoritative server timestamps.
- Explicit policy-level authorization for intentionally uncapped actions.
- Idempotent financial requests, budget reservation, settlement, release, and reversal state.
- Append-only settlement and compensating reversal records.
- Immutable audit events containing request, actor, agent, fleet, organization, policy decision,
  spend decision, amount, currency, timestamp, and execution result.

## Enforcement boundary

`POST /api/v1/financial-actions` is the execution boundary. The permission and spend evaluation
endpoints remain available for previews and backwards compatibility, but only the financial-action
gateway invokes the sandbox financial adapter.

The gateway rejects an action before adapter invocation when the agent, fleet, or organization is
not enabled, no policy allows the action, a mandatory budget is absent, or a configured budget
would be exceeded.

## Sandbox boundary

The adapter simulates execution and returns a deterministic sandbox reference. No external banking
or payment provider is used. Governance decisions, reservations, settlements, reversals, spend
records, and audit records are persisted by the backend.
