import base64
import hashlib
from urllib.parse import parse_qs, urlsplit

from starlette.testclient import TestClient

from whoop_mcp.remote import create_http_app
from whoop_mcp.storage import MemoryStore

ORIGIN = "https://shared.example.com"
PREFIX = "/mcp/whoop"
RESOURCE = ORIGIN + PREFIX + "/"
CALLBACK = "https://chatgpt.com/connector/oauth/test"


def test_shared_host_full_oauth_and_resource_isolation():
    app, provider = create_http_app(ORIGIN, store=MemoryStore(), shared_host=True)
    with TestClient(app, base_url=ORIGIN, follow_redirects=False) as client:
        assert client.get(PREFIX).headers["location"] == RESOURCE
        assert client.get(PREFIX + "/").status_code == 401
        assert client.get("/mcp").status_code == 404
        assert client.post("/register", json={}).status_code == 404
        metadata = client.get("/.well-known/oauth-protected-resource" + PREFIX + "/").json()
        assert metadata["resource"] == RESOURCE
        assert metadata["authorization_servers"] == [ORIGIN + PREFIX]
        auth = client.get("/.well-known/oauth-authorization-server" + PREFIX).json()
        assert auth["issuer"] == ORIGIN + PREFIX
        for key, suffix in (
            ("authorization_endpoint", "/authorize"),
            ("token_endpoint", "/token"),
            ("registration_endpoint", "/register"),
        ):
            assert auth[key] == ORIGIN + PREFIX + suffix
        registered = client.post(
            PREFIX + "/register",
            json={
                "redirect_uris": [CALLBACK],
                "token_endpoint_auth_method": "none",
                "scope": "whoop:read",
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
            },
        )
        assert registered.status_code == 201
        identity = registered.json()["client_id"]
        verifier = "v" * 64
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        authorization = {
            "client_id": identity,
            "redirect_uri": CALLBACK,
            "response_type": "code",
            "scope": "whoop:read",
            "state": "state",
            "resource": RESOURCE,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        rejected = client.get(
            PREFIX + "/authorize",
            params={**authorization, "resource": ORIGIN + "/mcp/garmin-connect/"},
        )
        assert rejected.status_code == 302
        assert parse_qs(urlsplit(rejected.headers["location"]).query)["error"] == [
            "invalid_request"
        ]
        response = client.get(PREFIX + "/authorize", params=authorization)
        assert response.status_code == 302
        consent = response.headers["location"]
        assert consent.startswith(ORIGIN + PREFIX + "/consent?")
        page = client.get(consent).text
        assert 'action="/mcp/whoop/consent"' in page
        assert "--shared-host" in page
        ticket = parse_qs(urlsplit(consent).query)["ticket"][0]
        with provider.state() as state:
            state["pending"][ticket]["approved"] = True
        response = client.get(consent)
        code = parse_qs(urlsplit(response.headers["location"]).query)["code"][0]
        token_args = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": identity,
            "redirect_uri": CALLBACK,
            "code_verifier": verifier,
            "resource": RESOURCE,
        }
        assert (
            client.post(
                PREFIX + "/token", data={**token_args, "resource": ORIGIN + "/mcp/myfitnesspal"}
            ).status_code
            == 400
        )
        assert (
            client.post(
                PREFIX + "/token", data={**token_args, "code_verifier": "x" * 64}
            ).status_code
            == 400
        )
        response = client.post(PREFIX + "/token", data=token_args)
        assert response.status_code == 200
        tokens = response.json()
        assert client.post(PREFIX + "/token", data=token_args).status_code == 400
        headers = {
            "Authorization": "Bearer " + tokens["access_token"],
            "Accept": "application/json, text/event-stream",
        }
        response = client.post(
            PREFIX + "/",
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "get_whoop_guide", "arguments": {}},
            },
        )
        assert response.status_code == 200 and "Das Kreb" in response.text
        assert (
            client.get(PREFIX + "/", headers={"Authorization": "Bearer garmin-token"}).status_code
            == 401
        )
        assert client.post(PREFIX + "/token", content=b"x" * 16385).status_code == 413
        refresh = {
            "grant_type": "refresh_token",
            "client_id": identity,
            "refresh_token": tokens["refresh_token"],
            "resource": RESOURCE,
        }
        rotated = client.post(PREFIX + "/token", data=refresh)
        assert rotated.status_code == 200
        assert client.post(PREFIX + "/token", data=refresh).status_code == 400
        assert client.post(PREFIX + "/", headers=headers, json={}).status_code == 401
        assert (
            client.post(
                PREFIX + "/revoke",
                data={
                    "client_id": identity,
                    "token": rotated.json()["refresh_token"],
                    "token_type_hint": "refresh_token",
                },
            ).status_code
            == 200
        )
