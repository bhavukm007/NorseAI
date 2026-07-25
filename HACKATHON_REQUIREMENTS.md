# Hackathon submission requirements

| Criterion | Repository evidence |
| --- | --- |
| Innovation | Mandatory governance gateway combining policy, hierarchical budgets, fleet control, execution, and evidence |
| Technical excellence | Layered FastAPI services/repositories, normalized SQLAlchemy models, Alembic migrations, typed React UI |
| Security | Persistent identities, scrypt hashes, rotating sessions, RBAC, rate limits, security headers, immutable audit |
| Financial Agent | Agent registration, fleet ownership, policy assignment, and governed sandbox actions |
| Governance Decision | Deterministic policy precedence and default denial |
| Budget Enforcement | Agent/fleet/organization transaction, daily, and monthly limits with reservation |
| Fleet Governance | Organization/fleet state and fleet-wide emergency stop |
| Auditability | Append-only records, request/correlation context, CSV and JSONL exports |
| Operator Experience | Authenticated Overview, Agents, Fleets, Policies, Budgets, Audit, and Emergency pages |
| AI Governance | Deterministic Assessment Lab with risk findings and executive exports |
| Demo readiness | [Demo script](docs/submission/demo-script.md) and [judging checklist](docs/submission/judging-checklist.md) |
| Production readiness | Docker images, Compose secret requirements, CI security scans, migration validation, PostgreSQL test |

## Submission boundary

The demonstrated financial adapter is sandboxed. Redis and OPA are provisioned services, not
active enforcement dependencies. No unsupported production integration is claimed.
