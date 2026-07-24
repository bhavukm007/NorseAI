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

Phase 2 adds no simulator, analytics, or WebSocket behavior.

## Phase 3 dashboard

The frontend now provides a responsive operator dashboard with a collapsible desktop sidebar,
mobile navigation drawer, sticky header, light and dark themes, live backend health polling,
governance status cards, system metrics, recent activity, and an AI chat experience. The dashboard
uses skeleton, empty/error-safe, and retryable states so intermittent API availability never
produces a blank screen.

The health card reads the public `/api/v1/health` endpoint every 30 seconds and on manual refresh.
Cards without a live API display an explicit unavailable state. The chat input remains disabled
until its Phase 4 backend endpoint exists. No Phase 2 authorization boundary is bypassed. Theme
preference is stored locally in the browser.

## Phase 4 AI governance simulator

The simulator now provides a complete local governance demonstration: a validated AI system
submission, six preconfigured demo scenarios, an animated assessment pipeline, risk and compliance
visualizations, rule findings, prioritized recommendations, and an executive decision report.
Assessments are retained in browser storage and can be reopened, compared, deleted, or exported as
PDF, JSON, and CSV. The scoring workflow is deterministic and complements the authenticated Phase
2 governance APIs without duplicating or weakening their authorization boundaries.

## Local development

### Backend

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m alembic upgrade head
uvicorn backend.app.main:app --reload
```

On macOS/Linux, activate with `source .venv/bin/activate`. The health endpoint is
`http://localhost:8000/api/v1/health`; interactive API documentation is at
`http://localhost:8000/docs`.

### Frontend

```powershell
cd frontend
npm ci
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
.\.venv\Scripts\python.exe -m ruff check backend tests migrations
.\.venv\Scripts\python.exe -m black --check backend tests migrations
.\.venv\Scripts\python.exe -m pytest --cov=backend --cov-report=term-missing
cd frontend
npm run lint
npm run format:check
npm run build
```

The frontend uses Vitest and Testing Library for dashboard component and interaction coverage:

```powershell
cd frontend
npm test
```

On Windows, invoke backend tools through `.\.venv\Scripts\python.exe -m ...` or activate `.venv`
first. A globally installed `pytest` launcher may use a different Python interpreter and will not
see the dependencies installed in `.venv`.

Install Git hooks with `pre-commit install`.
