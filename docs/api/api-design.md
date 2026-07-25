# API design

## Conventions

- Base path: `/api/v1`
- Media type: JSON, except CSV and JSONL audit exports
- Authentication: `Authorization: Bearer <access-token>`
- Pagination: `offset` (minimum 0) and `limit` (1–500)
- Errors: `{"error":{"code":"stable_code","message":"Human-readable message"}}`
- Validation errors additionally include `details`
- Request tracing: clients may send `X-Request-ID` and `X-Correlation-ID`; valid values are echoed
  and included in audit context

The public endpoint is `GET /health`. API documentation is available only when
`APP_DOCS_ENABLED=true`.

## Authentication

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/login` | Verify a persistent enabled user; issue access and refresh tokens |
| POST | `/auth/refresh` | Rotate a valid refresh token and issue a new access token |
| POST | `/auth/logout` | Revoke the current session |
| GET | `/auth/me` | Return the current persistent principal |
| POST | `/auth/users/{id}/disable` | Admin: disable user and revoke sessions |
| POST | `/auth/users/{id}/enable` | Admin: enable user |

Access claims require `exp`, `iat`, `nbf`, `iss`, `aud`, `sub`, `username`, `role`, `sid`, `ver`,
and `typ=access`. Authentication also checks the stored user, current role and token version,
enabled state, session ownership, session expiry, and revocation state.

## Authorization matrix

| Capability | Admin | Operator | Auditor | Viewer |
| --- | ---: | ---: | ---: | ---: |
| Read governance resources | Yes | Yes | Yes | Yes |
| Create/update agents, policies, assignments, limits, fleets | Yes | Yes | No | No |
| Evaluate or execute actions | Yes | Yes | No | No |
| Delete core resources | Yes | No | No | No |
| Emergency status changes and reversals | Yes | No | No | No |
| Audit list/export | Yes | No | Yes | No |
| User enable/disable | Yes | No | No | No |

## Governance resources

| Area | Endpoints |
| --- | --- |
| Agents | `POST/GET /agents`, `GET/PATCH/DELETE /agents/{id}` |
| Policies | `POST/GET /policies`, `GET/PATCH/DELETE /policies/{id}` |
| Assignments | `POST/GET /permissions`, `DELETE /permissions/{id}` |
| Decision preview | `POST /permissions/evaluate` |
| Agent limits | `POST/GET /spend-limits`, `GET/PATCH/DELETE /spend-limits/{id}` |
| Spend preview | `POST /spend/evaluate` |
| Agent status | `POST /agents/{id}/enable|disable|suspend` |
| Organizations | `POST/GET /organizations` |
| Fleets | `POST/GET /fleets`, `GET/PATCH /fleets/{id}` |
| Fleet status | `POST /fleets/{id}/enable|disable|emergency-stop` |
| Fleet limits | `POST /fleets/{id}/spend-limits`, `GET /fleet-spend-limits` |
| Organization limits | `POST /organizations/{id}/spend-limits`, `GET /organization-spend-limits` |
| Financial actions | `POST/GET /financial-actions`, `POST /financial-actions/{id}/reverse` |
| Audit | `GET /audit-logs`, `GET /audit-logs/export?format=csv|jsonl` |
| Dashboard | `GET /overview` |

## Financial action contract

`POST /financial-actions` accepts an agent, idempotency key, payment/transfer/refund type,
resource, positive amount, ISO-style three-letter currency, and decision context.

The service:

1. resolves agent, fleet, and organization;
2. rejects any non-enabled scope;
3. evaluates assigned policy using deterministic precedence;
4. requires agent, fleet, and organization budgets unless the policy explicitly allows uncapped
   spend;
5. locks applicable limits and reserves budget;
6. invokes the sandbox adapter only after authorization;
7. settles or releases the reservation and writes immutable evidence.

Repeating an idempotency key for the same agent returns the original action without executing or
spending twice. Reversal appends compensating records; it does not mutate settled ledger history.

## Audit filtering and export

`GET /audit-logs` supports `search`, `actor`, `fleet_id`, `organization_id`, `policy_id`, `action`,
`result`, `date_from`, and `date_to`, plus pagination. Export returns up to 500 newest rows in CSV
or newline-delimited JSON with the same schema, including decision and tracing fields.

## Rate limits

Login, authentication APIs, financial actions, and audit export use configurable fixed-window,
process-local limits. A rejected request returns HTTP 429 and `Retry-After`. For horizontally
scaled deployment, replace this implementation with a shared store.
