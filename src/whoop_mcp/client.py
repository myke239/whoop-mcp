"""Allowlisted WHOOP v2 reads with bounded responses and explicit pagination."""

import json
from datetime import UTC, datetime
from uuid import UUID

import httpx

from . import __version__
from .auth import Auth, WhoopError
from .tls import context

BASE = "https://api.prod.whoop.com/developer"
COLLECTIONS = {
    "cycles": "/v2/cycle",
    "recovery": "/v2/recovery",
    "sleep": "/v2/activity/sleep",
    "workouts": "/v2/activity/workout",
}
DETAILS = {
    "cycle": "/v2/cycle/{}",
    "cycle_sleep": "/v2/cycle/{}/sleep",
    "cycle_recovery": "/v2/cycle/{}/recovery",
    "sleep": "/v2/activity/sleep/{}",
    "workout": "/v2/activity/workout/{}",
}
SINGLETONS = {"profile": "/v2/user/profile/basic", "body": "/v2/user/measurement/body"}


def timestamp(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Timestamps must include a UTC offset")
    return parsed


def window(start=None, end=None):
    values = {k: timestamp(v) for k, v in {"start": start, "end": end}.items() if v}
    if len(values) == 2:
        delta = values["end"] - values["start"]
        if not 0 < delta.total_seconds() <= 366 * 86400:
            raise ValueError("Use an increasing range of at most 366 days")
    return {k: v.isoformat() for k, v in values.items()}


def project(value):
    """Omit member identity and contact fields from ordinary training reads."""
    if isinstance(value, dict):
        return {
            k: project(v)
            for k, v in value.items()
            if k not in {"user_id", "email", "first_name", "last_name"}
        }
    if isinstance(value, list):
        return [project(v) for v in value]
    return value


class WhoopClient:
    def __init__(self, auth=None, http=None):
        self.auth = auth or Auth()
        self.http = http or httpx.Client(
            verify=context(),
            timeout=httpx.Timeout(30, connect=10),
            follow_redirects=False,
            headers={"User-Agent": "whoop-mcp-das-kreb/" + __version__},
        )

    def _get(self, path, params=None, identity=False):
        token = self.auth.access_token()
        try:
            with self.http.stream(
                "GET", BASE + path, params=params, headers={"Authorization": "Bearer " + token}
            ) as response:
                if response.status_code != 200:
                    code = {
                        401: "AUTH_REQUIRED",
                        403: "SCOPE_REQUIRED",
                        404: "NOT_FOUND",
                        429: "RATE_LIMITED",
                    }.get(response.status_code, "UPSTREAM_ERROR")
                    raise WhoopError(code)
                raw = bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 2 * 1024 * 1024:
                        raise WhoopError("RESPONSE_TOO_LARGE")
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise WhoopError("INVALID_RESPONSE")
                return {
                    "source": "whoop_api_v2",
                    "fetched_at": datetime.now(UTC).isoformat(),
                    "data": data if identity else project(data),
                }
        except httpx.HTTPError:
            raise WhoopError("NETWORK_ERROR") from None
        except (ValueError, TypeError):
            raise WhoopError("INVALID_RESPONSE") from None

    def collection(self, kind, start=None, end=None, limit=25, next_token=None):
        if kind not in COLLECTIONS or type(limit) is not int or not 1 <= limit <= 25:
            raise ValueError("Use a known collection and limit 1–25")
        params = {**window(start, end), "limit": limit}
        if next_token is not None:
            if not isinstance(next_token, str) or not 1 <= len(next_token) <= 4096:
                raise ValueError("Invalid pagination token")
            params["nextToken"] = next_token
        result = self._get(COLLECTIONS[kind], params)
        data = result["data"]
        if not isinstance(data.get("records"), list) or len(data["records"]) > limit:
            raise WhoopError("INVALID_RESPONSE")
        result["pagination"] = {
            "next_token": data.get("next_token"),
            "complete": not bool(data.get("next_token")),
        }
        return result

    def detail(self, kind, identifier):
        if kind not in DETAILS:
            raise ValueError("Unknown detail type")
        if kind.startswith("cycle"):
            if type(identifier) is not int or not 0 < identifier < 2**63:
                raise ValueError("Cycle ID must be a positive 64-bit integer")
        else:
            identifier = str(UUID(str(identifier)))
        return self._get(DETAILS[kind].format(identifier))

    def singleton(self, kind):
        if kind not in SINGLETONS:
            raise ValueError("Unknown singleton")
        return self._get(SINGLETONS[kind], identity=(kind == "profile"))

    def history(self, kind, start, end, max_records=250):
        if type(max_records) is not int or not 1 <= max_records <= 250:
            raise ValueError("History is bounded to 250 records")
        records, seen, token = [], set(), None
        for _ in range(10):
            page = self.collection(kind, start, end, min(25, max_records - len(records)), token)
            records.extend(page["data"]["records"])
            token = page["pagination"]["next_token"]
            if not token or len(records) >= max_records:
                return {"records": records, "complete": not bool(token), "next_token": token}
            if token in seen:
                raise WhoopError("PAGINATION_LOOP")
            seen.add(token)
        return {"records": records, "complete": False, "next_token": token}
