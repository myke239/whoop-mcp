import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

import pytest
from starlette.testclient import TestClient

from whoop_mcp.remote import OwnerProvider, create_http_app, public_origin, valid_callback
from whoop_mcp.storage import MemoryStore

ORIGIN = "https://whoop.example.com"
CALLBACK = "https://chatgpt.com/connector_platform_oauth_redirect"


@pytest.mark.parametrize(
    "callback",
    [
        "https://evil.test/connector_platform_oauth_redirect",
        "https://chatgpt.com.evil.test/connector_platform_oauth_redirect",
        "https://chatgpt.com/evil",
        "http://chatgpt.com/connector_platform_oauth_redirect",
        "https://chatgpt.com/connector/oauth/",
        "https://chatgpt.com/connector/oauth/x/y",
    ],
)
def test_callback_restrictions(callback):
    assert not valid_callback(callback)


@pytest.mark.parametrize(
    "origin",
    ["http://example.com", "https://x.test/path", "https://user@x.test", "https://x.test?token=x"],
)
def test_origin_restrictions(origin):
    with pytest.raises(ValueError):
        public_origin(origin)


def connection():
    store = MemoryStore()
    app, provider = create_http_app(ORIGIN, store=store)
    return TestClient(app, base_url=ORIGIN), provider


def register(client):
    response = client.post(
        "/register",
        json={
            "redirect_uris": [CALLBACK],
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": "whoop:read",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["client_id"]


def authorize(client, provider, client_id):
    verifier = "v" * 64
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    response = client.get(
        "/authorize",
        params={
            "client_id": client_id,
            "redirect_uri": CALLBACK,
            "response_type": "code",
            "scope": "whoop:read",
            "state": "owner-state",
            "resource": ORIGIN + "/mcp",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302, response.text
    consent = response.headers["location"]
    page = client.get(consent)
    assert "APPROVE" in page.text
    ticket = parse_qs(urlsplit(consent).query)["ticket"][0]
    # Offline owner approval simulation; production can only approve interactively.
    with provider.state() as state:
        state["pending"][ticket]["approved"] = True
    response = client.get(consent, follow_redirects=False)
    code = parse_qs(urlsplit(response.headers["location"]).query)["code"][0]
    return {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": verifier,
        "client_id": client_id,
        "redirect_uri": CALLBACK,
        "resource": ORIGIN + "/mcp",
    }


def test_http_oauth_pkce_replay_refresh_and_revoke():
    client, provider = connection()
    with client:
        response = client.get("/mcp")
        assert response.status_code == 401
        assert "resource_metadata" in response.headers["www-authenticate"]
        metadata = client.get("/.well-known/oauth-authorization-server").json()
        assert "S256" in metadata["code_challenge_methods_supported"]
        identifier = register(client)
        data = authorize(client, provider, identifier)
        bad = client.post("/token", data={**data, "code_verifier": "x" * 64})
        assert bad.status_code == 400
        response = client.post("/token", data=data)
        assert response.status_code == 200, response.text
        tokens = response.json()
        assert client.post("/token", data=data).status_code == 400
        headers = {
            "Authorization": "Bearer " + tokens["access_token"],
            "Accept": "application/json, text/event-stream",
        }
        result = client.post(
            "/mcp",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
        )
        assert result.status_code == 200, result.text
        refresh = {
            "grant_type": "refresh_token",
            "client_id": identifier,
            "refresh_token": tokens["refresh_token"],
            "resource": ORIGIN + "/mcp",
        }
        assert (
            client.post("/token", data={**refresh, "resource": "https://evil.test"}).status_code
            == 400
        )
        rotated = client.post("/token", data=refresh)
        assert rotated.status_code == 200, rotated.text
        assert client.post("/token", data=refresh).status_code == 400
        assert client.post("/mcp", headers=headers, json={}).status_code == 401
        revoked = client.post(
            "/revoke",
            data={
                "client_id": identifier,
                "token": rotated.json()["refresh_token"],
                "token_type_hint": "refresh_token",
            },
        )
        assert revoked.status_code == 200, revoked.text
        assert (
            client.post(
                "/token", data={**refresh, "refresh_token": rotated.json()["refresh_token"]}
            ).status_code
            == 400
        )


def test_http_boundaries_and_registration():
    client, _ = connection()
    with client:
        assert client.get("/health").json()["read_only"]
        assert client.get("/health", headers={"Host": "evil.test"}).status_code == 403
        assert client.get("/health", headers={"Origin": "https://evil.test"}).status_code == 403
        assert client.post("/register", content=b"x" * 16385).status_code == 413
        assert (
            client.post("/register", json={"redirect_uris": ["https://evil.test/cb"]}).status_code
            == 400
        )
        for _ in range(121):
            response = client.get("/health")
        assert response.status_code == 429


def test_origin_change_refused():
    store = MemoryStore()
    with OwnerProvider(ORIGIN, store).state():
        pass
    with (
        pytest.raises(ValueError, match="Origin changed"),
        OwnerProvider("https://new.example.com", store).state(),
    ):
        pass
