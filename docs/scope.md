# Scope and Garmin comparison

The reference is the owner's Garmin Connect MCP project. WHOOP receives the same
engineering categories: account authorization, encrypted local state, bounded tools,
guided plugin skills, remote OAuth, managed installers, native bundles, CI, public
documentation, privacy materials and explicit live-verification evidence.

| Garmin capability | WHOOP implementation |
| --- | --- |
| Activities, recovery and sleep | Official v2 workout, cycle, recovery and sleep reads |
| HRV and physiological context | Recovery HRV, resting HR, SpO2 and skin temperature when scored |
| Activity comparisons | Bounded period summaries and comparisons with missingness |
| Daily coaching evidence | Exact cycle joins and explicit local-date rules |
| Workout builders and scheduling | Unavailable in the public WHOOP member API |
| Journal, hydration and activity edits | Unavailable in the public WHOOP member API |
| FIT archives and continuous samples | Unavailable in the public WHOOP member API |
| Local stdio / remote HTTP | Supported; separate local and remote authorization |
| Cross-platform distribution | Managed installers and target-OS native build workflow |
| Das Kreb branding | Same approved logo and vendor identity |

The member access-revocation endpoint remains an explicit action in WHOOP settings;
it is not an assistant-callable destructive tool. Legacy v1 ID mapping is unnecessary
for new v2 records. Trusted-partner lab/requisition endpoints require separate partner
credentials and are outside this fitness connector.

Source: [WHOOP official API](https://developer.whoop.com/api/), checked 2026-10-22.
No undocumented mobile endpoints are used, and no unsupported write parity is claimed.
