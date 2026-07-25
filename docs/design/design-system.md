# Design system

NorseAI uses an enterprise control-room visual language built from CSS tokens in
`frontend/src/styles/tokens.css`.

- Light and dark color schemes use semantic surface, text, border, accent, success, and warning
  tokens.
- Operator pages share `PageHeader`, `DataState`, `StatusBadge`, panels, tables, toolbars, and
  form controls.
- Lucide icons always accompany text or accessible labels; color is not the only status signal.
- Layout supports persistent/collapsed desktop navigation and a keyboard-operable mobile drawer.
- Loading, empty, error, offline, and success states are explicit.
- Motion respects reduced-motion preferences.

Feature CSS is separated into layout, dashboard, operator, simulator, feedback, chat legacy
styles, and responsive layers through `global.css`. New UI should reuse semantic tokens and shared
governance components rather than introduce page-specific color constants.
