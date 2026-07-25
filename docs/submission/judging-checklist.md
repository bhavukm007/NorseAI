# Final judging checklist

## Environment

- [ ] Copy `.env.example` to `.env` and set a 32+ character JWT secret and strong operator/database
      passwords.
- [ ] Apply `python -m alembic upgrade head`.
- [ ] Confirm `GET /api/v1/health` and operator sign-in.
- [ ] Start the frontend and open `/dashboard`.
- [ ] Seed or create an organization, fleet, agent, policy assignment, and limits.

## Product walkthrough

- [ ] Overview shows live governance data.
- [ ] Financial agent, fleet, policy, and hierarchical budgets are visible.
- [ ] Governed sandbox action settles and appears in recent decisions.
- [ ] Idempotent replay does not duplicate execution or spend.
- [ ] Fleet emergency stop prevents execution.
- [ ] Audit event is filterable and exports as CSV and JSONL.
- [ ] AI Assessment Lab completes and exports an executive report.
- [ ] Light/dark themes, keyboard focus, and responsive navigation work.

## Release gates

- [ ] Backend Ruff, Black, tests, migration SQL, and dependency audit pass.
- [ ] Frontend ESLint, Prettier, tests, production build, and critical dependency audit pass.
- [ ] PostgreSQL integration passes when `POSTGRES_TEST_DATABASE_URL` is configured.
- [ ] `docker compose config --quiet` passes with required secrets.
- [ ] `git diff --check` is clean.
- [ ] No secrets, build output, caches, screenshots falsely presented as product UI, or temporary
      test directories are committed.
- [ ] README and submission narration match the current product.
