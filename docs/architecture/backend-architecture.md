# Backend architecture

The FastAPI backend uses explicit layers:

```text
api/v1/routes      HTTP contracts, status codes, dependencies, RBAC
api/dependencies   database sessions, principal validation, service composition
services           governance and financial business rules
repositories       persistence queries, locking, and audit insertion
models             SQLAlchemy schema and append-only event guards
schemas            Pydantic request/response validation
adapters           external execution boundary; currently sandbox-only
core               settings, logging, security primitives, rate limiting
```

Routes do not perform governance decisions. They validate requests and delegate to services.
Services coordinate policies, hierarchical budgets, reservations, execution, and audit records in
one database transaction. Repositories isolate query ordering and row locking.

`create_app()` owns settings, middleware, handlers, session factory, bootstrap-user creation, and
lifespan behavior. Tests create independent applications with SQLite; production uses PostgreSQL
and Alembic migrations.

Stable `AppError` responses cover authentication, authorization, not-found, conflict, and
validation outcomes. SQLAlchemy integrity conflicts are rolled back by the session boundary.
