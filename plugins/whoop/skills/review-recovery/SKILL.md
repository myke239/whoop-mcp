---
name: review-recovery
description: Review WHOOP recovery, HRV, resting heart rate, sleep and naps with explicit units and missingness.
---

# WHOOP recovery evidence

Call `get_whoop_guide` first. Use `get_whoop_day` for exact cycle joins with a local YYYY-MM-DD and IANA timezone. Physiological cycles differ from calendar days; state the date rule used.

For multiweek reviews, query recovery and sleep collections or period summaries. Use `get_whoop_cycle_recovery` and `get_whoop_cycle_sleep` when a specific cycle is relevant. Sleep collections include naps; cycle sleep is the primary sleep. Stage and zone durations use milliseconds. HRV uses ms, resting HR bpm, respiratory rate breaths/min, SpO2 %, skin temperature °C. WHOOP sleep scores are percentages.

Preserve unscored records and pagination status. Do not treat a missing recovery as zero or reuse yesterday's recovery as today's. Describe trends without diagnosing illness or promising performance. Do not infer causal effects from associations. If pain or illness is reported, avoid declaring the user medically safe to train.

Do not retrieve name/email unless the user asks for their profile. Never request account credentials in chat or include health records in bug reports. If the server reports a scope or login error, ask the user to reauthorize locally.
