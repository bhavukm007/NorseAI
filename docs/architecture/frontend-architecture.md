# Frontend Architecture

The React/TypeScript frontend follows feature and responsibility boundaries:

- `app` defines route composition.
- `components/layout` provides persistent navigation and the workspace header.
- `components/dashboard` and `components/chat` provide reusable presentation modules.
- `features/dashboard` composes the operator dashboard.
- `hooks` isolates live API synchronization.
- `providers` contains small cross-cutting theme and notification contexts.
- `styles` separates tokens, base rules, application layout, dashboard, chat, feedback, and
  responsive behavior behind one stable `global.css` entry point.
- `lib/api` remains the typed HTTP boundary.

Server state is kept inside focused hooks and refreshed efficiently. Device preferences use browser
storage. Global UI state is limited to theme and transient toasts, avoiding a state-management
dependency while the application remains compact.
