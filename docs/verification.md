# Verification evidence

Evidence is recorded as checks run, not inferred from implemented features.

## Local development — 2026-10-22

- Windows Python 3.13: 57 offline tests passed, including real stdio initialize/list/call and graceful EOF shutdown.
- HTTP OAuth exercised through the actual SDK routes: discovery, registration, local-consent
  simulation, wrong PKCE rejection, successful code exchange, code replay rejection,
  authenticated MCP initialization, resource mismatch rejection, refresh rotation and revocation.
- Synthetic data only. No WHOOP account connected during these checks.
- Windows clean managed installer passed: wheel installed into an isolated prefix,
  installed launcher version checked, real stdio initialize/list/call passed, bundled
  plugin copied and absolute executable configuration checked.
- Windows native executable built and passed version, real stdio and plugin-copy checks.
- Fixed an SDK stdio-wrapper handle ownership issue that produced a frozen bootloader
  shutdown traceback. Explicit process-owned streams passed the native EOF regression check.
- Dependency audit after upgrading pip to 26.2.2: no known vulnerabilities; the local
  project itself is unpublished on PyPI and is not covered by dependency advisory lookup.
- WHOOP public host reachable with native OS certificate trust; unauthenticated member
  endpoint returned the expected 401. This is network reachability, not account validation.
- Cross-platform CI run [39851885641](https://github.com/myke239/whoop-mcp/actions/runs/39851885641)
  passed all six OS/Python combinations and dependency audit at commit 097a690:
  Windows/macOS/Linux × Python 3.12/3.13, 56 tests per job, wheel builds and clean
  managed installer/installed MCP/plugin checks. Final EOF and prefix-safety changes
  trigger a fresh run before merge.

## Required before live acceptance

- Run target-OS native bundle builds and record their results.
- Owner creates/configures WHOOP OAuth app locally and completes browser consent.
- Run verify and exercise representative cycle/recovery/sleep/workout reads with owner's consent.
- Verify privacy projection, units, score states and pagination against real responses.
- Connect the public HTTPS MCP endpoint to the owner's ChatGPT account, then check phone access.
- Record target-OS installer/bundle results and distinguish unsigned from signed distribution.

Do not commit live WHOOP responses or token-bearing callback URLs as evidence.
