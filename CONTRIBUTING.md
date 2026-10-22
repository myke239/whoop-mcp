# Contributing

Use Python 3.12+ in a project-local virtual environment. Install `.[dev,remote]`.
Work on a branch, add meaningful regression checks, open a PR and wait for checks.

Run `python -m ruff check src tests scripts`, `python -m ruff format --check src tests scripts`,
`python -m pytest -q`, `python -m build` and `python -m pip check`.
CI checks Windows, macOS and Linux and exercises the real stdio protocol.

Never commit tokens, client secrets, private API responses or real health fixtures.
Live WHOOP and ChatGPT acceptance tests are opt-in and excluded from CI.
Document errors using stable error codes and redacted diagnostics.

All account reads must use the fixed WHOOP endpoint allowlists. No arbitrary URLs,
private endpoints or partner lab APIs. Do not add account writes without documented
member scopes and an operation-specific review/commit design.
