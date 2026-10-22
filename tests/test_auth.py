import time
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx
import pytest

from whoop_mcp.auth import SCOPES, Auth, WhoopError, redirect_uri
from whoop_mcp.storage import MemoryStore


def configured(handler=None):
    store = MemoryStore()
    auth = Auth(
        store,
        httpx.Client(
            transport=httpx.MockTransport(
                handler
                or (
                    lambda r: httpx.Response(
                        200,
                        json={
                            "access_token": "ACCESS",
                            "refresh_token": "REFRESH",
                            "expires_in": 3600,
                            "token_type": "Bearer",
                        },
                    )
                )
            )
        ),
    )
    auth.configure("client", "secret", "http://127.0.0.1:8937/callback")
    return auth


def callback(auth):
    query = parse_qs(urlsplit(auth.begin()).query)
    assert "secret" not in str(query)
    return "http://127.0.0.1:8937/callback?code=CODE&state=" + query["state"][0]


def test_login_state_and_replay():
    auth = configured()
    url = callback(auth)
    with pytest.raises(WhoopError, match="INVALID_CALLBACK"):
        auth.complete(url + "wrong")
    auth.complete(url)
    assert auth.access_token() == "ACCESS"
    with pytest.raises(WhoopError, match="INVALID_CALLBACK"):
        auth.complete(url)


def test_whoop_callback_with_scope_exchanges_code_once():
    requests = []

    def handler(request):
        requests.append(parse_qs(request.content.decode()))
        return httpx.Response(
            200,
            json={
                "access_token": "ACCESS",
                "refresh_token": "REFRESH",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        )

    auth = configured(handler)
    state = parse_qs(urlsplit(auth.begin()).query)["state"][0]
    # Match the observed provider shape, using only synthetic code/state values.
    url = "http://127.0.0.1:8937/callback?" + urlencode(
        {"code": "SYNTHETIC-CODE", "scope": " ".join(SCOPES), "state": state}
    )
    with pytest.raises(WhoopError, match="INVALID_CALLBACK"):
        auth.complete(url.replace(state, "wrong-state"))
    assert not requests
    auth.complete(url)
    assert requests == [
        {
            "grant_type": ["authorization_code"],
            "client_id": ["client"],
            "client_secret": ["secret"],
            "redirect_uri": ["http://127.0.0.1:8937/callback"],
            "code": ["SYNTHETIC-CODE"],
        }
    ]
    assert auth.access_token() == "ACCESS"
    with pytest.raises(WhoopError, match="INVALID_CALLBACK"):
        auth.complete(url)
    assert len(requests) == 1


@pytest.mark.parametrize(
    "suffix",
    [
        "&scope=read%3Asleep&scope=offline",
        "&scope=",
        "&scope=unknown%3Ascope",
        "&scope=read%3Asleep&extra=1",
        "&scope=read%3Asleep&state=extra",
    ],
)
def test_scope_callback_preserves_validation(suffix):
    auth = configured(lambda r: pytest.fail("Invalid callback must not exchange a code"))
    with pytest.raises(WhoopError, match="INVALID_CALLBACK"):
        auth.complete(callback(auth) + suffix)


@pytest.mark.parametrize("suffix", ["&state=duplicate", "&code=extra", "#fragment"])
def test_callback_pollution(suffix):
    auth = configured()
    with pytest.raises(WhoopError):
        auth.complete(callback(auth) + suffix)


def test_expiry_and_refresh_rotation():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "access_token": "rotated",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        )

    auth = configured(handler)
    with auth.store.transaction() as state:
        state["token"] = {"access_token": "old", "refresh_token": "old-refresh", "expires_at": 0}
    assert auth.access_token() == "rotated"
    assert b"old-refresh" in requests[0].content
    assert auth.store.state["token"]["refresh_token"] == "new-refresh"
    auth.access_token()
    assert len(requests) == 1
    auth.logout()
    with pytest.raises(WhoopError, match="AUTH_REQUIRED"):
        auth.access_token()


def test_expired_login():
    auth = configured()
    url = callback(auth)
    auth.store.state["login"]["expires_at"] = time.time() - 1
    with pytest.raises(WhoopError):
        auth.complete(url)


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/callback",
        "http://localhost:8937/callback",
        "http://127.0.0.1:80/callback",
        "http://user@127.0.0.1:8937/callback",
        "http://127.0.0.1:8937/callback?extra=1",
    ],
)
def test_redirect_allowlist(url):
    with pytest.raises(ValueError):
        redirect_uri(url)
