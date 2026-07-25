# Phase 02: Governance Engine

## Delivered

- SQLAlchemy models and Alembic migration for users, agents, policies, assignments, spend limits,
  immutable spend records, and audit records.
- Layered APIs for agent, policy, assignment, and spend-limit administration.
- Permission and spend evaluation plus emergency agent controls.
- Admin, Operator, Auditor, and Viewer role enforcement.
- Prioritized allow, deny, and context-based conditional policies with default denial.

Policies match exact actions/resources or `*`. Evaluation uses descending priority,
DENY → CONDITIONAL → ALLOW effect precedence, oldest creation time, then UUID. Conditional
policies apply only when all declared conditions equal the supplied context.

Spend evaluation checks transaction, UTC daily, and UTC monthly limits. Successful legacy spend
evaluations append spend records used for cumulative calculations. Limit rows are locked during
evaluation on PostgreSQL.

Audit rows retain historical identifiers and PostgreSQL triggers reject updates and deletes.
Phase 08 later replaced the original stateless token boundary with persistent users and revocable
sessions; current requirements are in
[security architecture](../architecture/security-architecture.md).

This document records Phase 02 delivery. Later phases added the operator UI, financial gateway,
fleets, hierarchical budgets, and hardened authentication.
