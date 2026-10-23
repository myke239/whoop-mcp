# Changelog

## 0.1.1 - 2026-10-22

- Add isolated shared-host OAuth and MCP routes at `/mcp/whoop/`, with a separate
  grant store and explicit `--shared-host` commands.

- Verify login through the profile endpoint so missing optional body measurements do
  not fail an otherwise valid connection. Live checks disclose unavailable data.
- Suppress routine HTTP request logs that can contain private record identifiers.

- Accept WHOOP's optional OAuth callback scope parameter while preserving state,
  expiry, callback-target and duplicate-parameter validation.
- Use an ASCII setup banner so Windows PowerShell displays it correctly.

## 0.1.0 — initial implementation

- Official WHOOP v2 member reads for cycles, recovery, sleep, workouts, profile and body measurements.
- Daily evidence with exact cycle joins; bounded summaries and period comparisons.
- Local OAuth login, encrypted OS-keyring-backed state and serialized token refresh.
- Stdio MCP and single-owner HTTP OAuth with local consent, PKCE, resource binding and revocation.
- Das Kreb Codex plugin with three guided skills.
- Managed Windows, macOS and Linux installers, native build workflow and public documentation.

Live WHOOP and ChatGPT/phone verification is recorded separately in docs/verification.md.
