# Verification evidence

Evidence is recorded as checks run, not inferred from implemented features.

## Local development — 2026-10-22

- Windows Python 3.13: first 50 offline tests passed, including real stdio initialize/list/call.
- HTTP OAuth exercised through the actual SDK routes: discovery, registration, local-consent
  simulation, wrong PKCE rejection, successful code exchange, code replay rejection,
  authenticated MCP initialization, resource mismatch rejection, refresh rotation and revocation.
- Synthetic data only. No WHOOP account connected during these checks.

## Required before live acceptance

- Finish packaging and installer verification; run all CI platforms and record their results.
- Owner creates/configures WHOOP OAuth app locally and completes browser consent.
- Run verify and exercise representative cycle/recovery/sleep/workout reads with owner's consent.
- Verify privacy projection, units, score states and pagination against real responses.
- Connect the public HTTPS MCP endpoint to the owner's ChatGPT account, then check phone access.
- Record target-OS installer/bundle results and distinguish unsigned from signed distribution.

Do not commit live WHOOP responses or token-bearing callback URLs as evidence.
