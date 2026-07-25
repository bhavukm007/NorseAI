# Frontend architecture

The React/TypeScript application is organized by product responsibility:

```text
app/router.tsx             protected route composition and lazy Assessment Lab loading
features/auth              sign-in, session context, protected-route boundary
features/dashboard         live operator overview
features/governance        agents, fleets, policies, budgets, audit, emergency pages
features/simulator         AI Assessment Lab, deterministic analysis, local history
components/layout          responsive application shell and navigation
providers                  theme and toast contexts
lib/api                    authenticated HTTP and audit download boundary
styles                     tokens and feature-scoped CSS
```

TanStack Query owns remote governance state and invalidation. Access-token session data uses
session storage and is cleared on expiry or authentication failure. The theme and validated,
bounded assessment history use browser storage. Operational governance pages do not substitute
fixtures for API data.

The primary route is `/dashboard`; `/assessment-lab` is a secondary, lazy-loaded workspace.
Protected routes redirect unauthenticated visitors to `/login`.
