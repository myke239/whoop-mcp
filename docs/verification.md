# Verification evidence

Evidence is recorded as checks run, not inferred from implemented features.

## Local development — 2026-10-22

- Windows Python 3.13: 57 offline tests passed, including real stdio initialize/list/call and graceful EOF shutdown.
- HTTP OAuth exercised through the actual SDK routes: discovery, registration, local-consent
  simulation, wrong PKCE rejection, successful code exchange, code replay rejection,
  authenticated MCP initialization, resource mismatch rejection, refresh rotation and revocation.
- Initial offline checks used synthetic data only; subsequent live evidence is below.
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
  managed installer/installed MCP/plugin checks.
- Final implementation run [39852206192](https://github.com/myke239/whoop-mcp/actions/runs/39852206192)
  passed all seven jobs with 57 tests per OS/Python job, including EOF shutdown and
  prefix-safety changes. PR #1 was merged only after these checks passed.
- Native release run [39852562577](https://github.com/myke239/whoop-mcp/actions/runs/39852562577)
  built and verified Windows, macOS 14 and Ubuntu 22.04 bundles: version, real MCP
  initialize/list/call, graceful EOF, bundled plugin copy, archives and SHA-256 manifests.
- Native Windows doctor also exercised the actual Windows OS keyring using an empty
  synthetic private directory. macOS/Linux live keyring sessions remain owner-environment checks.
- Downloaded all three published archives and independently verified their SHA-256
  manifests, safe archive paths and Unix executable permission bits.
- The downloaded Windows executable did not pass startup on the owner's machine:
  CreateProcess returned WinError 5 (Access is denied). Avast autosandbox.log recorded
  that exact executable as a sandbox candidate with a Terminate result at 13:55:54
  America/Los_Angeles on 2026-10-22. No protection was disabled or bypassed. The local
  build and Windows CI passed, but that does not establish downloaded-binary acceptance
  under Avast. Use the tested managed Python installer while this remains unresolved.

## Authenticated empty-account acceptance - 2026-10-22

- Owner completed browser authorization after the callback-scope fix in PR #4.
- `verify` passed using an authenticated profile read without printing identity fields.
- Actual stdio MCP checks passed for guide, profile, all four collections, all four
  period summaries, a local-date view and period comparison.
- The test account has no recorded history. Both bounded and unfiltered latest reads
  returned empty collections. WHOOP returned NOT_FOUND for body measurements; this is
  disclosed as unavailable rather than treated as a failed login.
- Populated details, pagination and unit values remain covered by synthetic tests only;
  an empty-account check does not verify those paths against populated live data.
- Routine HTTP request-path logging is disabled to avoid printing record identifiers.

## Remaining acceptance

- Verify privacy projection, units, score states and pagination against real responses.
- Connect the public HTTPS MCP endpoint to the owner's ChatGPT account, then check phone access.
- All current native archives are unsigned; no publisher verification or notarization is claimed.
- Resolve native Windows download acceptance through normal signing/reputation and
  antivirus vendor review before claiming production-ready native distribution.

After local authorization, run the explicit opt-in acceptance harness:

```powershell
& .venv/Scripts/python.exe scripts/verify_live.py --live --timezone America/Los_Angeles
```

It starts an actual stdio MCP client and exercises representative reads, pagination,
detail lookups, summaries and a local-date view. It prints statuses and sample counts;
it does not persist health records. This script is never part of default tests or CI.

Do not commit live WHOOP responses or token-bearing callback URLs as evidence.
