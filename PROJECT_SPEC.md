# PROJECT_SPEC

## Executive Summary
NorseAI is an enterprise governance platform for autonomous financial agents. Phase 1 establishes
the deployable application boundary and developer experience without implementing product logic.

## Phase 1 scope

- A versioned FastAPI API and React application shell.
- Environment-based, validated configuration with no committed secrets.
- Structured logs, health reporting, and explicit dependency boundaries.
- PostgreSQL, Redis, and OPA services provisioned for future phases but unused by product logic.
- Reproducible container builds and automated quality verification.

## Non-functional requirements

- Python 3.11+ and Node.js 20+.
- Cross-platform local workflows and Linux production containers.
- Strict type checking at language and schema boundaries.
- Least-privilege container execution where supported.
- Modular API, application, domain, repository, and UI feature boundaries.

## Deferred capabilities

Governance decisions, policy evaluation, spend controls, operational dashboards, persistent domain
entities, authentication, and agent simulation remain outside Phase 1.

## Phase 2 scope

Phase 2 adds the governance backend: normalized persistence, agent and policy administration,
permission evaluation, spend limits, immutable audit history, emergency controls, JWT
authentication, and RBAC. User interfaces and operational analytics remain deferred.

Spend controls evaluate transaction, UTC daily, and UTC monthly limits against immutable approved
spend records. Permission conflicts are deterministic. Audit history is append-only at both the
application and database layers, and authentication requires signed, time-bounded,
issuer/audience-scoped JWTs.
