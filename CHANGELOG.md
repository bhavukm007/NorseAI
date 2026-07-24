# Changelog

## Phase 04

- Added the interactive AI Governance Simulator with six auto-filled assessment scenarios.
- Added animated governance processing, risk scoring, compliance KPIs, rule evaluation, and
  prioritized recommendations.
- Added Recharts radar, donut, severity, category, and assessment-trend visualizations.
- Added persistent local assessment history with report reopening, comparison, and deletion.
- Added professional executive reports with PDF, JSON, and CSV exports.

All notable changes to NorseAI are documented here.

## [Unreleased]

### Added

- Phase 3 premium operator dashboard with responsive navigation, system status cards, health
  polling, metrics, recent activity, AI chat, persisted light/dark themes, animated notifications,
  loading skeletons, error recovery, and mobile drawer behavior.
- Frontend Vitest and Testing Library coverage for dashboard rendering, navigation, status,
  chat, theme preference, loading and error states, and notifications.
- Production review removed dashboard fixtures and simulated chat responses, modularized frontend
  styles, expanded accessibility and hook coverage, and optimized social metadata.
- Phase 2 governance models, Alembic migration, layered REST APIs, policy evaluation, spend limits,
  immutable audit history, emergency controls, JWT authentication, RBAC, and tests.
- Hardened Phase 2 with cumulative spend evaluation, deterministic policy conflict resolution,
  required JWT claims and issuer/audience validation, database audit immutability triggers,
  complete ORM relationships, query indexes, pagination, stable errors, and PostgreSQL integration
  coverage.
- Phase 1 modular FastAPI foundation with versioned health API, typed settings, structured logging,
  CORS, dependency injection boundary, and tests.
- React, TypeScript, and Vite application shell with routing, responsive layout, sidebar,
  dashboard placeholder, not-found page, and typed API client.
- Backend and frontend Dockerfiles plus Compose services for PostgreSQL, Redis, and OPA.
- Ruff, Black, pytest, ESLint, Prettier, EditorConfig, pre-commit, and GitHub Actions CI.
- Local development, validation, environment, and scope documentation.

## v0.1.0

- Repository initialized.
