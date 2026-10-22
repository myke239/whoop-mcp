"""Opt-in authenticated MCP acceptance. Prints statuses/counts, never health records."""

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def verify(timezone):
    ZoneInfo(timezone)
    now = datetime.now(UTC)
    start = (now - timedelta(days=14)).isoformat()
    end = now.isoformat()
    params = StdioServerParameters(command=sys.executable, args=["-m", "whoop_mcp.cli", "serve"])
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()

        async def call(name, arguments):
            result = await session.call_tool(name, arguments)
            data = json.loads(result.content[0].text)
            if result.isError or "error" in data:
                if (
                    name == "get_whoop_body_measurements"
                    and not result.isError
                    and data.get("error") == "NOT_FOUND"
                ):
                    print(name + ": UNAVAILABLE (WHOOP returned NOT_FOUND)", flush=True)
                    return data
                raise RuntimeError(name + ": " + data.get("error", "MCP_ERROR"))
            print(name + ": PASS", flush=True)
            return data

        await call("get_whoop_guide", {})
        await call("get_whoop_body_measurements", {})
        await call("get_whoop_profile", {})
        for kind in ("cycles", "recovery", "sleep", "workouts"):
            result = await call("list_whoop_" + kind, {"start": start, "end": end, "limit": 2})
            records = result["data"]["records"]
            print(
                kind
                + ": "
                + str(len(records))
                + " sample records; complete="
                + str(result["pagination"]["complete"])
            )
            if result["pagination"]["next_token"]:
                await call(
                    "list_whoop_" + kind,
                    {
                        "start": start,
                        "end": end,
                        "limit": 2,
                        "next_token": result["pagination"]["next_token"],
                    },
                )
            if records and kind == "cycles":
                await call("get_whoop_cycle", {"cycle_id": records[0]["id"]})
                # A pending cycle may legitimately have no recovery or primary sleep.
            elif records and kind in ("sleep", "workouts"):
                singular = "workout" if kind == "workouts" else "sleep"
                await call("get_whoop_" + singular, {singular + "_id": records[0]["id"]})
            await call("summarize_whoop_period", {"kind": kind, "start": start, "end": end})
        await call(
            "get_whoop_day",
            {
                "calendar_date": now.astimezone(ZoneInfo(timezone)).date().isoformat(),
                "timezone": timezone,
            },
        )
        await call(
            "compare_whoop_periods",
            {
                "kind": "recovery",
                "first_start": start,
                "first_end": (now - timedelta(days=7)).isoformat(),
                "second_start": (now - timedelta(days=7)).isoformat(),
                "second_end": end,
            },
        )
    print(
        "Authenticated MCP checks completed; unavailable data is reported above. No account records written to disk."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Explicitly allow authenticated WHOOP reads"
    )
    parser.add_argument("--timezone", required=True, help="Owner's IANA timezone")
    args = parser.parse_args()
    if not args.live:
        parser.error("Pass --live to authorize account reads; this is excluded from CI")
    try:
        asyncio.run(verify(args.timezone))
    except Exception:
        print(
            "Live acceptance did not pass. Run local doctor/verify; do not share credentials or health output.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
