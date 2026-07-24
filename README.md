# NorseAI

Enterprise governance platform for autonomous financial agents.

## Phase 1 foundation

This branch contains only the production foundation:

- Versioned FastAPI service with typed environment settings, JSON logging, dependency injection,
  CORS, OpenAPI, and a health endpoint.
- React, TypeScript, and Vite application shell with routing, responsive layout, a sidebar, and a
  deliberately non-functional dashboard placeholder.
- Docker Compose services for the API, web application, PostgreSQL, Redis, and OPA.
- Ruff, Black, pytest, ESLint, Prettier, EditorConfig, pre-commit, and GitHub Actions.

Dashboard and simulator behavior remain intentionally deferred.

## Phase 2 governance engine

The backend provides authenticated `/api/v1` APIs for agent and policy management, permission
assignment and evaluation, spend limits, emergency agent controls, and read-only audit history.
JWT claims carry `username`, `role`, and a required user UUID in `sub`; supported roles are
`admin`, `operator`, `auditor`, and `viewer`.

JWTs must include `exp`, `iat`, `nbf`, `iss`, `aud`, `sub`, `username`, and `role`. Configure
`APP_JWT_SECRET`, `APP_JWT_ISSUER`, and `APP_JWT_AUDIENCE`; non-development environments refuse to
start without a secret.

Permission decisions are ordered by descending priority, then DENY → CONDITIONAL → ALLOW, then
oldest creation timestamp, then UUID. This makes every conflict deterministic.

`POST /api/v1/spend/evaluate` evaluates transaction, daily, and monthly limits in that order.
Allowed evaluations are recorded as spend so later daily/monthly decisions use cumulative totals.
All timestamps are evaluated in UTC.

Apply the PostgreSQL schema before starting the API:

```powershell
alembic upgrade head
```

Phase 2 adds no dashboard, monitoring, simulator, analytics, notification, or WebSocket behavior.

## Local development

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn backend.app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate`. The health endpoint is
`http://localhost:8000/api/v1/health`; interactive API documentation is at
`http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

The web application is served at `http://localhost:5173`.

### Full stack

Copy `.env.example` to `.env`, replace the development database password, then run:

```powershell
docker compose up --build
```

The containerized frontend is available at `http://localhost:3000`.

## Quality checks

```powershell
ruff check backend tests
black --check backend tests
pytest --cov=backend
cd frontend
npm run lint
npm run format:check
npm run build
```

Install Git hooks with `pre-commit install`.
