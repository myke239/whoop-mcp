# Tools, units and limits

All 15 tools declare read-only, non-destructive and idempotent MCP annotations.
`get_whoop_guide` needs no account. Other tools require local WHOOP authorization.

| Tool | Contract |
| --- | --- |
| get_whoop_guide | Capabilities, unavailable features, exact units, bounds and first-use rules |
| get_whoop_profile | Explicit sensitive profile read including name and email |
| get_whoop_body_measurements | Current height m, weight kg, max HR bpm |
| list_whoop_cycles | One page of physiological cycles and day strain |
| list_whoop_recovery | One page of recovery and scored physiological metrics |
| list_whoop_sleep | One page of sleep, including naps |
| list_whoop_workouts | One page of recorded workouts |
| get_whoop_cycle | Exact positive integer cycle ID |
| get_whoop_cycle_recovery | Recovery for an exact cycle ID |
| get_whoop_cycle_sleep | Primary sleep for an exact cycle ID |
| get_whoop_sleep | Exact v2 sleep UUID |
| get_whoop_workout | Exact v2 workout UUID |
| get_whoop_day | YYYY-MM-DD plus IANA timezone, exact cycle joins |
| summarize_whoop_period | Collection kind, offset-aware start/end, descriptive statistics |
| compare_whoop_periods | Two periods, counts/missingness and second-minus-first mean differences |

Collection `limit` is 1–25. Return `next_token` as `next_token` on the next call;
the client maps it to upstream `nextToken`. A list response contains source, fetched_at,
data and pagination completeness. Singletons/details also carry source and fetched_at.

Summary kinds are `cycles`, `recovery`, `sleep`, and `workouts`. Summary history is capped
at 250 records and 10 requests per collection. Each comparison uses two such histories.
An increasing period must not exceed 366 days. A summary with `complete: false` is a
partial sample, not a full-period total; continue collection pagination for raw records.
Day views fetch at most 250 cycles and 250 workouts plus primary sleep/recovery details
for matching cycles. Records are assigned to the local date by start timestamp.

WHOOP physiological cycles need not align with calendar days. Primary sleep and recovery
are joined by cycle ID, not guessed timestamps. Cycle sleep is not a list of naps.
List timestamps must include an offset; local date views use IANA zones and account for DST.

Recovery is %, HRV ms, resting/max/average HR bpm, SpO2 %, skin temperature °C,
respiratory rate breaths/min, energy kJ, distance/elevation m. Stage durations and HR-zone
durations are milliseconds. Body height is m and mass kg. Strain is WHOOP's nonlinear
0–21 scale; neither cycle nor workout strain is summed by analytics.

Statistics include SCORED records only. Missing, boolean, non-finite, pending and
unscorable values do not become zeros. Each metric reports observations, missing count,
mean, min and max. No training recommendation, diagnosis or causal attribution is generated
by the arithmetic tools. Unexpected responses produce stable, redacted errors.

Each upstream response is capped at 2 MiB and has a 30-second HTTP timeout. HTTP MCP
requests are capped at 1 MiB; OAuth requests at 16 KiB. Remote service limits include
120 requests/minute, 16 concurrent HTTP requests, 128 clients, 32 pending consents,
256 access tokens and 128 refresh tokens. Remote access tokens last one hour; refresh
tokens rotate and last 30 days. Pending consent lasts five minutes and codes 60 seconds.

No arbitrary URL tool, API proxy, private mobile endpoint, location track or partner lab
endpoint is exposed. The v1 migration mapper and upstream grant deletion are not tools.
Revoke WHOOP authorization using WHOOP account settings.
