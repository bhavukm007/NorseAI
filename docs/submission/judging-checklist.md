# Final judging checklist

## Before presenting

- [ ] Copy `.env.example` to `.env` and use development-only local values.
- [ ] Start FastAPI and confirm `/api/v1/health` reports healthy.
- [ ] Start the frontend and open the dashboard.
- [ ] Complete one assessment so history and comparison have representative data.
- [ ] Verify PDF, JSON, and CSV downloads in the presentation browser.
- [ ] Verify light and dark themes.
- [ ] Keep the presentation viewport at 1280px wide or larger.
- [ ] Close unrelated tabs and disable distracting system notifications.

## Product walkthrough

- [ ] Dashboard loads without layout shift.
- [ ] One-click demo launches from the dashboard.
- [ ] All eight assessment stages complete.
- [ ] Risk, compliance, and five visualization views render.
- [ ] Governance rule statuses and priority recommendations are readable.
- [ ] Executive report opens and exports.
- [ ] History persists after reload, comparison works, and deletion is confirmed by removal.
- [ ] Keyboard focus is visible and the skip link reaches main content.
- [ ] Mobile navigation opens, closes with Escape, and restores focus.
- [ ] Offline backend state offers a retry action without blocking the simulator.

## Release gates

- [ ] Frontend production build passes.
- [ ] Frontend tests and ESLint pass.
- [ ] Backend tests, Ruff, and Black checks pass.
- [ ] `git diff --check` is clean.
- [ ] No secrets, debug output, generated builds, or temporary test directories are committed.
- [ ] README installation and demo steps match the final product.
- [ ] Current Phase 05 commit is pushed to the submission branch.
