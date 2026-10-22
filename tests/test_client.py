import httpx
import pytest

from whoop_mcp.auth import WhoopError
from whoop_mcp.client import WhoopClient, window


class FakeAuth:
    def access_token(self):
        return "PRIVATE"


def client(handler):
    return WhoopClient(FakeAuth(), httpx.Client(transport=httpx.MockTransport(handler)))


def test_read_boundary_projection_and_pagination():
    def handler(request):
        assert request.method == "GET"
        assert request.url.host == "api.prod.whoop.com"
        assert request.url.path == "/developer/v2/activity/workout"
        assert request.headers["authorization"] == "Bearer PRIVATE"
        assert request.url.params["limit"] == "25"
        return httpx.Response(
            200,
            json={
                "records": [
                    {"id": "x", "user_id": 123, "score_state": "PENDING_SCORE", "score": None}
                ],
                "next_token": "next",
            },
        )

    result = client(handler).collection("workouts")
    assert result["pagination"] == {"complete": False, "next_token": "next"}
    assert "user_id" not in result["data"]["records"][0]
    assert result["data"]["records"][0]["score"] is None


@pytest.mark.parametrize(
    "status,code",
    [
        (401, "AUTH_REQUIRED"),
        (403, "SCOPE_REQUIRED"),
        (404, "NOT_FOUND"),
        (429, "RATE_LIMITED"),
        (500, "UPSTREAM_ERROR"),
        (302, "UPSTREAM_ERROR"),
    ],
)
def test_sanitized_errors(status, code):
    with pytest.raises(WhoopError, match=code):
        client(lambda r: httpx.Response(status, text="secret body")).singleton("body")


@pytest.mark.parametrize(
    "kind,identifier",
    [("workout", "../evil"), ("cycle", -1), ("cycle", True), ("cycle", 2**64), ("evil", "x")],
)
def test_detail_validation(kind, identifier):
    with pytest.raises(ValueError):
        client(lambda r: pytest.fail("No network permitted")).detail(kind, identifier)


@pytest.mark.parametrize("limit", [0, 26, True, -1])
def test_limit_validation(limit):
    with pytest.raises(ValueError):
        client(lambda r: pytest.fail("No network permitted")).collection("sleep", limit=limit)


def test_bounds_and_timestamps():
    with pytest.raises(ValueError):
        window("2026-01-01", "2026-02-01")
    with pytest.raises(ValueError):
        window("2026-02-01T00:00:00Z", "2026-01-01T00:00:00Z")
    assert window("2026-01-01T00:00:00Z")["start"].endswith("+00:00")


def test_pagination_loop_and_cap():
    api = client(lambda r: httpx.Response(200, json={"records": [{"id": 1}], "next_token": "same"}))
    with pytest.raises(WhoopError, match="PAGINATION_LOOP"):
        api.history("cycles", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")
    assert not api.history("cycles", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z", 1)["complete"]


def test_response_size_limit():
    with pytest.raises(WhoopError, match="RESPONSE_TOO_LARGE"):
        client(lambda r: httpx.Response(200, content=b"x" * (2 * 1024 * 1024 + 1))).singleton(
            "body"
        )
