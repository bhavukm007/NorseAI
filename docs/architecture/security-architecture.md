# Security architecture

## Identity and sessions

- Bootstrap credentials come from `APP_OPERATOR_USERNAME` and `APP_OPERATOR_PASSWORD`.
- Passwords are stored using Python `scrypt` with per-password random salt.
- Access JWTs are signed with HS256 and validate issuer, audience, lifetime, type, user, role,
  session, and token version.
- Refresh tokens are random, stored only as SHA-256 hashes in PostgreSQL, rotated on use, and
  invalidated by logout.
- Disabled users and revoked or expired sessions are rejected on every protected request.

## Authorization and request controls

- Admin, Operator, Auditor, and Viewer RBAC is enforced as route dependencies.
- Login, authentication, financial execution, and audit export are rate limited.
- CORS origins are explicit.
- API and Nginx responses set CSP, frame denial, no-sniff, referrer, and permissions policies.
- HSTS is enabled for staging and production (and test verification), not local development.
- Inputs use bounded Pydantic schemas; database conflicts use stable error responses.

## Evidence controls

- Audit records contain actor and historical references, request/correlation IDs, structured
  metadata, immutable decision context, policy version, policy/spend decisions, and execution
  result.
- Audit and spend records are append-only at ORM and PostgreSQL trigger layers.
- Reversals append compensating records rather than rewriting history.

## Environment variables

All backend variables use the `APP_` prefix.

| Variable | Default | Production guidance |
| --- | --- | --- |
| `APP_ENVIRONMENT` | `development` | Set `production` |
| `APP_DEBUG` | `false` | Must remain false |
| `APP_LOG_LEVEL` | `INFO` | Use `INFO` or stricter |
| `APP_API_V1_PREFIX` | `/api/v1` | Change only with matching frontend config |
| `APP_DOCS_ENABLED` | `true` | Disable in production |
| `APP_CORS_ORIGINS` | local Vite origin | Restrict to deployed UI origins |
| `APP_DATABASE_URL` | local PostgreSQL | Use managed credentials/TLS as applicable |
| `APP_JWT_SECRET` | unset | Required; minimum 32 characters |
| `APP_JWT_ALGORITHM` | `HS256` | Only supported value |
| `APP_JWT_ISSUER` | `norseai` | Set deployment-specific issuer if needed |
| `APP_JWT_AUDIENCE` | `norseai-api` | Set deployment-specific audience |
| `APP_OPERATOR_USERNAME` | `admin` | Bootstrap identity |
| `APP_OPERATOR_PASSWORD` | development demo value | Required to change in production |
| `APP_ACCESS_TOKEN_MINUTES` | `60` | 5–1440 |
| `APP_REFRESH_TOKEN_DAYS` | `7` | 1–90 |
| `APP_LOGIN_RATE_LIMIT` | `10` | Requests per window |
| `APP_AUTH_RATE_LIMIT` | `60` | Requests per window |
| `APP_FINANCIAL_RATE_LIMIT` | `60` | Requests per window |
| `APP_AUDIT_EXPORT_RATE_LIMIT` | `10` | Requests per window |
| `APP_RATE_LIMIT_WINDOW_SECONDS` | `60` | 1–3600 |
| `APP_HSTS_MAX_AGE` | `31536000` | Set according to TLS policy |
| `APP_CSP_POLICY` | API-deny policy | Override only after security review |
| `APP_REDIS_URL` | local Redis | Provisioned extension point |
| `APP_OPA_URL` | local OPA | Provisioned extension point |

Frontend build configuration uses `VITE_API_BASE_URL`. Compose additionally requires
`JWT_SECRET`, `OPERATOR_PASSWORD`, and `POSTGRES_PASSWORD`, and supports `POSTGRES_DB`,
`POSTGRES_USER`, `JWT_ISSUER`, and `JWT_AUDIENCE`.

## Scaling limitation

Rate-limit counters are process-local. A production deployment with multiple API replicas must
move counters to a shared store before claiming globally consistent limits.
