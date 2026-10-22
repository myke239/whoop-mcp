---
name: daily-check-in
description: Use WHOOP daily recovery and sleep evidence to discuss a user's planned training without changing the account.
---

# Daily WHOOP check-in

Call `get_whoop_guide`, then fetch the requested local date with `get_whoop_day`. Ask for the IANA timezone if it cannot be established. Explain which physiological cycle, primary sleep and recorded workouts are present. Fetch naps separately if relevant.

Combine the retrieved evidence with the user's stated plan, fatigue, soreness and preferences. If a baseline matters, fetch a bounded prior period and disclose observation counts; do not present an invented baseline. Separate recorded metrics from user-reported context and your interpretation. Missing values do not mean low recovery.

Discuss practical adjustments without diagnosing, treating WHOOP as medical clearance, or claiming that a score guarantees performance. Do not create or edit workouts, alarms or journal entries: the official API does not provide those actions. This is an advisory conversation only.
