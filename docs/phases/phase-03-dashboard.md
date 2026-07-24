# Phase 3: Dashboard

## Objective

Deliver a polished, responsive operator control center without changing the completed governance
engine or prematurely implementing Phase 4 simulator behavior.

## Delivered

- Responsive application shell with persistent/collapsible desktop navigation and mobile drawer.
- Sticky project header with system state, session identity, theme, refresh, and notifications.
- Reusable metric cards for backend, governance, simulator, policies, AI, and API throughput.
- Live public health polling with latency measurement, synchronization time, errors, and retry.
- Explicit unavailable states for operational metrics and activity until authenticated APIs exist.
- Disabled AI chat surface that clearly identifies the Phase 4 backend dependency.
- Device-local light/dark theme persistence and an animated success/error/warning/info toast layer.
- Skeleton loading, actionable error, and graceful fallback states.
- Reserved, navigable routes for scheduled product modules so navigation never falls through to a
  blank or broken screen.

## Architecture

Dashboard code is grouped by responsibility:

- `components/layout` owns application chrome and responsive navigation.
- `components/dashboard` contains reusable operational panels and cards.
- `components/chat` contains the conversational surface.
- `hooks/useSystemHealth` owns polling, latency, synchronization, and retry behavior.
- `providers` owns cross-cutting theme and notification state.
- `features/dashboard` composes the Phase 3 page.

The public health endpoint is the only live data source used in Phase 3. Governance list endpoints
remain protected by Phase 2 JWT/RBAC rules. No fixture values or simulated chat responses are shown
as real data. The dashboard emits a single refresh event so panels can refresh without coupling the
header to feature internals.

## Accessibility and responsiveness

Semantic landmarks, named icon buttons, status announcements, focusable actions, reduced-motion
support, and contrast-aware theme tokens are built in. The six-card grid contracts to three, two,
and one columns; content panels reflow without horizontal scrolling; navigation becomes an
off-canvas drawer below tablet width.

## Verification

- Vitest and Testing Library cover dashboard rendering, sidebar routing and keyboard dismissal,
  active state, health hook behavior, status skeletons, successful and failed health checks,
  disabled chat behavior, activity empty state, theme persistence, and toast dismissal.
- TypeScript, ESLint, Prettier, Vite production build, and the complete backend test suite remain
  part of the acceptance gate.
