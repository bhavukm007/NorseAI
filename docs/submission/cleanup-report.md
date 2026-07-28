# Repository cleanup report

This report is intentionally non-destructive. No cleanup candidate was deleted or moved during
release hardening.

## KEEP

- `PresentationAssets/Screenshots/*.png` — curated, consistently named submission screenshots.
- `frontend/public/og.jpg` — active social-preview asset referenced by the frontend.
- `ppt-images/10-assessment-lab.png` — covers the assessment surface not present in the curated
  screenshot set under the same filename.
- `.env.example` — required configuration template; it contains placeholders/demo defaults rather
  than production credentials.

## DELETE

- `ppt-images/norseai_screens.db`
- `ppt-images/norseai_screens_8011.db`
- `PresentationAssets/Runtime/norseai_screenshots.db`

  These are runtime SQLite capture databases, not application source or required seed data.

- `.pytest-tmp/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`, Python `__pycache__/`, and
  `frontend/dist/` — generated test, lint, coverage, bytecode, and build outputs. They should remain
  untracked and may be removed before packaging.

- `ppt-images/norseai-dashboard-images.zip` — generated archive duplicates image assets already
  available as individual files and can be recreated.

## MOVE

- Review the useful images in `ppt-images/*.png` and move any selected final submission images into
  `PresentationAssets/Screenshots/` using the curated numbering convention. The two directories
  overlap in subject matter but are not byte-for-byte duplicates.
- After selection, move any retained capture-only source material to an external submission-assets
  archive if it is not intended to ship with the application repository.

## IGNORE

- `.env` — local runtime configuration. It must remain excluded from Git because it may contain
  secrets; distribute `.env.example` instead.
- `.venv/` and `frontend/node_modules/` — local dependency environments, reproducible from the
  lock and requirement files.
- Docker named volumes `postgres_data` and `redis_data` — runtime state managed outside the source
  tree; do not add them to version control.

Before deleting or moving any listed item, confirm which screenshot set is used by the final
submission package.
