# Phase 2: Governance Engine

## Delivered

- SQLAlchemy 2.x models and Alembic migration for users, agents, policies, permission assignments,
  spend limits, and immutable audit records.
- Layered APIs for agent/policy/spend CRUD, permission evaluation, and emergency controls.
- JWT bearer authentication with Admin, Operator, Auditor, and Viewer role enforcement.
- Prioritized allow, deny, and context-based conditional policy evaluation with default denial.

Policies assigned to an agent match exact actions/resources or `*`. They are evaluated by
descending priority, DENY → CONDITIONAL → ALLOW effect precedence, oldest creation timestamp, and
finally UUID. Conditional policies apply when every condition equals its evaluation context value.
No match means deny.

Spend evaluation checks transaction, daily, and monthly limits. Successful evaluations create
immutable spend records used for cumulative UTC day/month calculations. Limit rows are locked
during evaluation to serialize concurrent decisions for the same agent and currency.

Audit rows are protected from UPDATE and DELETE by database triggers. Historical user, agent, and
policy identifiers are stored without cascading foreign keys, while view-only ORM relationships
resolve them when related records still exist.

Every governance API requires a JWT except health and API documentation. Tokens must contain
`exp`, `iat`, `nbf`, `iss`, `aud`, `sub`, `username`, and `role`, and must pass signature, issuer,
audience, lifetime, and UUID validation.

## Exclusions

Dashboard, UI, simulator, monitoring, analytics, reporting, notifications, workers, WebSockets,
Grafana, Prometheus, and payment integration remain deferred.
