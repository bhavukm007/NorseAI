# Phase 08: Security hardening and production readiness

## Delivered

- Persistent users, scrypt password hashes, expiring access tokens, rotating hashed refresh
  sessions, logout revocation, user disablement, and revoked-session protection.
- CSP, HSTS, frame, referrer, no-sniff, and permissions headers.
- Configurable rate limiting for authentication, financial actions, and audit export.
- Audit request/correlation IDs, structured metadata, immutable decision context, and policy
  versions.
- Production secret validation and Compose defaults that require explicit credentials.
- Patched Python dependencies and a frontend transitive dependency override.
- CI dependency auditing, Bandit scanning, migration SQL validation, PostgreSQL integration,
  production builds, and container verification.
- Regression coverage for authentication edge cases, rate limiting, headers, and audit integrity.

## Known boundary

Rate limits are process-local. React Router's current audit advisory targets RSC/server-action mode,
which this client-only SPA does not use; CI fails on critical advisories while retaining the latest
stable router line.
