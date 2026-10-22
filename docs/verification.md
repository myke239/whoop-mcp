# Verification evidence

Evidence is recorded as checks run, not inferred from implemented features.

## Local development — 2026-10-22

- Windows Python 3.13: 52 offline tests passed before tunnel tests were added, including real stdio initialize/list/call.
- HTTP OAuth exercised through the actual SDK routes: discovery, registration, local-consent
  simulation, wrong PKCE rejection, successful code exchange, code replay rejection,
  authenticated MCP initialization, resource mismatch rejection, refresh rotation and revocation.
- Synthetic data only. No WHOOP account connected during these checks.
- Windows clean managed installer passed: wheel installed into an isolated prefix,
  installed launcher version checked, real stdio initialize/list/call passed, bundled
  plugin copied and absolute executable configuration checked.
- Windows native executable built and passed version, real stdio and plugin-copy checks.
- Dependency audit after upgrading pip to 26.2.2: no known vulnerabilities; the local
  project itself is unpublished on PyPI and is not covered by dependency advisory lookup.
- WHOOP public host reachable with native OS certificate trust; unauthenticated member
  endpoint returned the expected 401. This is network reachability, not account validation.
- First cross-platform CI run found a missing test-scratch parent on fresh checkouts;
  fixed in conftest.py and rerun. Final CI evidence will be recorded after completion.

## Required before live acceptance

- Finish packaging and installer verification; run all CI platforms and record their results.
- Owner creates/configures WHOOP OAuth app locally and completes browser consent.
- Run verify and exercise representative cycle/recovery/sleep/workout reads with owner's consent.
- Verify privacy projection, units, score states and pagination against real responses.
- Connect the public HTTPS MCP endpoint to the owner's ChatGPT account, then check phone access.
- Record target-OS installer/bundle results and distinguish unsigned from signed distribution.

Do not commit live WHOOP responses or token-bearing callback URLs as evidence.
