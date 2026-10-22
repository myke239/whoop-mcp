"""MCP tools for the full documented WHOOP member read surface."""

from functools import wraps

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__
from .analytics import METRICS, daily_evidence, summarize
from .auth import WhoopError
from .client import WhoopClient, window


def create_server(client=None, **settings):
    client = client or WhoopClient()
    server = FastMCP(
        "WHOOP · Das Kreb",
        instructions="Use get_whoop_guide first. Preserve units, score states, pagination and missingness. WHOOP tools are read-only.",
        **settings,
    )

    def tool(fn):
        @wraps(fn)
        def safe(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except WhoopError as error:
                return {"error": error.code}
            except (ValueError, KeyError, TypeError):
                return {"error": "INVALID_INPUT_OR_RESPONSE"}
            except Exception:
                # Never expose HTTP exceptions, token-bearing URLs or OS keyring details.
                return {
                    "error": "LOCAL_SERVICE_ERROR",
                    "action": "Run whoop-mcp doctor in your local terminal",
                }

        return server.tool(
            annotations=ToolAnnotations(
                readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True
            )
        )(safe)

    @tool
    def get_whoop_guide() -> dict:
        """Capabilities, units, limits, privacy and first-use guidance. No account needed."""
        return {
            "version": __version__,
            "author": "Das Kreb",
            "api": "WHOOP official v2",
            "capabilities": [
                "profile",
                "body measurements",
                "cycles",
                "recovery",
                "sleep",
                "workouts",
                "daily evidence",
                "period summaries",
                "period comparison",
            ],
            "unsupported": [
                "workout creation or scheduling",
                "journal edits",
                "alarms",
                "continuous heart-rate samples",
                "GPS",
                "steps",
            ],
            "units": METRICS,
            "body_units": {"height_meter": "m", "weight_kilogram": "kg", "max_heart_rate": "bpm"},
            "limits": {
                "page_size": 25,
                "history_records": 250,
                "history_requests": 10,
                "window_days": 366,
            },
            "rules": [
                "Use offset-aware ISO timestamps; local dates require an IANA timezone.",
                "Preserve SCORED, PENDING_SCORE and UNSCORABLE states.",
                "Missing values are not zero; strain must not be summed.",
                "Profile reveals name/email only when explicitly requested.",
                "Data is descriptive evidence, not medical clearance.",
                "Configure/login locally; never request credentials in chat.",
            ],
        }

    @tool
    def get_whoop_profile() -> dict:
        """Explicitly retrieve WHOOP member profile including name/email. Sensitive identity data."""
        return client.singleton("profile")

    @tool
    def get_whoop_body_measurements() -> dict:
        """Current body measurements: height m, weight kg and maximum heart rate bpm."""
        return client.singleton("body")

    @tool
    def list_whoop_cycles(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
        next_token: str | None = None,
    ) -> dict:
        """Page through physiological cycles and day strain. Times require UTC offsets."""
        return client.collection("cycles", start, end, limit, next_token)

    @tool
    def list_whoop_recovery(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
        next_token: str | None = None,
    ) -> dict:
        """Page recovery, HRV ms, resting HR bpm, SpO2 % and skin temperature °C."""
        return client.collection("recovery", start, end, limit, next_token)

    @tool
    def list_whoop_sleep(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
        next_token: str | None = None,
    ) -> dict:
        """Page sleep and naps, stage durations in milliseconds and respiratory rate."""
        return client.collection("sleep", start, end, limit, next_token)

    @tool
    def list_whoop_workouts(
        start: str | None = None,
        end: str | None = None,
        limit: int = 25,
        next_token: str | None = None,
    ) -> dict:
        """Page recorded workouts, strain, heart rate, distance and HR-zone milliseconds."""
        return client.collection("workouts", start, end, limit, next_token)

    @tool
    def get_whoop_cycle(cycle_id: int) -> dict:
        """Retrieve one physiological cycle by its integer ID."""
        return client.detail("cycle", cycle_id)

    @tool
    def get_whoop_cycle_recovery(cycle_id: int) -> dict:
        """Retrieve recovery joined to an exact integer cycle ID."""
        return client.detail("cycle_recovery", cycle_id)

    @tool
    def get_whoop_cycle_sleep(cycle_id: int) -> dict:
        """Retrieve primary sleep for an exact integer cycle ID."""
        return client.detail("cycle_sleep", cycle_id)

    @tool
    def get_whoop_sleep(sleep_id: str) -> dict:
        """Retrieve one sleep by v2 UUID, preserving score state and stage milliseconds."""
        return client.detail("sleep", sleep_id)

    @tool
    def get_whoop_workout(workout_id: str) -> dict:
        """Retrieve one workout by v2 UUID with recorded HR zones and strain."""
        return client.detail("workout", workout_id)

    @tool
    def get_whoop_day(calendar_date: str, timezone: str) -> dict:
        """Local-date evidence with exact cycle joins. YYYY-MM-DD and IANA timezone required."""
        return daily_evidence(client, calendar_date, timezone)

    @tool
    def summarize_whoop_period(kind: str, start: str, end: str) -> dict:
        """Descriptive cycle/recovery/sleep/workout statistics, bounded to 250 records."""
        window(start, end)
        if kind not in METRICS:
            raise ValueError("Unknown collection")
        history = client.history(kind, start, end)
        return {
            "kind": kind,
            "start": start,
            "end": end,
            "source": "whoop_api_v2",
            "complete": history["complete"],
            "next_token": history["next_token"],
            **summarize(kind, history["records"]),
        }

    @tool
    def compare_whoop_periods(
        kind: str, first_start: str, first_end: str, second_start: str, second_end: str
    ) -> dict:
        """Compare two bounded periods; disclose counts and missingness. No causal claims."""
        first = summarize_whoop_period(kind, first_start, first_end)
        second = summarize_whoop_period(kind, second_start, second_end)
        if "error" in first or "error" in second:
            return {"first": first, "second": second}
        delta = {
            name: {
                "unit": value["unit"],
                "mean_difference": round(second["metrics"][name]["mean"] - value["mean"], 3)
                if value["mean"] is not None and second["metrics"][name]["mean"] is not None
                else None,
            }
            for name, value in first["metrics"].items()
        }
        return {
            "first": first,
            "second": second,
            "second_minus_first": delta,
            "limitations": "Descriptive comparison; unequal counts and confounding can affect interpretation.",
        }

    return server
