"""Descriptive evidence: preserve missingness, states, units and physiological cycles."""

import math
import statistics
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .client import timestamp

METRICS = {
    "recovery": {
        "recovery_score": "%",
        "hrv_rmssd_milli": "ms",
        "resting_heart_rate": "bpm",
        "spo2_percentage": "%",
        "skin_temp_celsius": "°C",
    },
    "cycles": {
        "strain": "WHOOP strain (0–21)",
        "kilojoule": "kJ",
        "average_heart_rate": "bpm",
        "max_heart_rate": "bpm",
    },
    "sleep": {
        "sleep_performance_percentage": "%",
        "sleep_consistency_percentage": "%",
        "sleep_efficiency_percentage": "%",
        "respiratory_rate": "breaths/min",
    },
    "workouts": {
        "strain": "WHOOP strain (0–21)",
        "kilojoule": "kJ",
        "average_heart_rate": "bpm",
        "max_heart_rate": "bpm",
        "distance_meter": "m",
        "altitude_gain_meter": "m",
    },
}


def numeric(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def summarize(kind, records):
    metrics = {}
    scored = [
        r for r in records if r.get("score_state") == "SCORED" and isinstance(r.get("score"), dict)
    ]
    for name, unit in METRICS[kind].items():
        values = [r["score"][name] for r in scored if numeric(r["score"].get(name))]
        metrics[name] = {
            "unit": unit,
            "observations": len(values),
            "missing": len(records) - len(values),
            "mean": round(statistics.mean(values), 3) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }
    return {
        "record_count": len(records),
        "scored_count": len(scored),
        "metrics": metrics,
        "interpretation": "Descriptive statistics. Missing and unscored values are not zero. Strain is nonlinear and is not summed.",
    }


def local_bounds(calendar_date, timezone):
    day = date.fromisoformat(calendar_date)
    zone = ZoneInfo(timezone)
    return (
        datetime.combine(day, time.min, zone).isoformat(),
        datetime.combine(day + timedelta(days=1), time.min, zone).isoformat(),
    )


def daily_evidence(client, calendar_date, timezone):
    start, end = local_bounds(calendar_date, timezone)
    # Fetch cycles by their own date window; join recovery and primary sleep by exact cycle ID.
    page = client.history("cycles", start, end)
    zone = ZoneInfo(timezone)
    day = date.fromisoformat(calendar_date)
    cycles = [
        r
        for r in page["records"]
        if r.get("start") and timestamp(r["start"]).astimezone(zone).date() == day
    ]
    joined = []
    from .auth import WhoopError

    for cycle in cycles:
        entry = {"cycle": cycle}
        for kind in ("cycle_recovery", "cycle_sleep"):
            try:
                entry[kind.removeprefix("cycle_")] = client.detail(kind, cycle["id"])["data"]
            except WhoopError as error:
                entry[kind.removeprefix("cycle_")] = {"unavailable": error.code}
        joined.append(entry)
    workouts = client.history("workouts", start, end)
    workouts["records"] = [
        r
        for r in workouts["records"]
        if r.get("start") and timestamp(r["start"]).astimezone(zone).date() == day
    ]
    return {
        "calendar_date": calendar_date,
        "timezone": timezone,
        "start": start,
        "end": end,
        "cycles": joined,
        "workouts": workouts,
        "cycles_complete": page["complete"],
        "date_rule": "Cycle and workout start in requested local calendar date; primary sleep and recovery joined by cycle ID.",
        "limitations": "WHOOP physiological cycles are not calendar days. Naps are available from the sleep collection. No diagnosis or medical clearance.",
    }
