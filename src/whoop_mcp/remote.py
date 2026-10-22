"""Single-owner OAuth MCP endpoint. WHOOP tokens never leave the local server."""

import hashlib
import html
import secrets
import shlex
import sys
import time
from contextlib import contextmanager
from urllib.parse import parse_qs, urlsplit

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    AuthorizeError,
    RefreshToken,
    RegistrationError,
    TokenError,
    construct_redirect_uri,
)
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.server.transport_security import TransportSecuritySettings
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from pydantic import AnyHttpUrl
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from .server import create_server
from .storage import Store, data_directory

READ_SCOPE = "whoop:read"


def public_origin(value):
    p = urlsplit(value)
    if (
        p.scheme != "https"
        or not p.hostname
        or p.username
        or p.password
        or p.port not in (None, 443)
        or p.path not in ("", "/")
        or p.query
        or p.fragment
    ):
        raise ValueError("Provide a public HTTPS origin without path, credentials or query")
    return "https://" + p.hostname.lower()


def valid_callback(value):
    p = urlsplit(str(value))
    return (
        p.scheme == "https"
        and p.hostname == "chatgpt.com"
        and p.port in (None, 443)
        and not p.username
        and not p.password
        and not p.query
        and not p.fragment
        and (
            p.path == "/connector_platform_oauth_redirect"
            or (
                p.path.startswith("/connector/oauth/")
                and len(p.path.removeprefix("/connector/oauth/")) > 0
                and "/" not in p.path.removeprefix("/connector/oauth/")
            )
        )
    )


def key(token):
    return hashlib.sha256(token.encode()).hexdigest()


def approval_command(ticket):
    args = [sys.executable, "-m", "whoop_mcp.cli", "remote", "approve", ticket]
    if sys.platform == "win32":
        return "& " + " ".join("'" + a.replace("'", "''") + "'" for a in args)
    return shlex.join(args)


class OwnerRefresh(RefreshToken):
    family: str


class OwnerProvider:
    def __init__(self, origin, store=None):
        self.origin = public_origin(origin)
        self.resource = self.origin + "/mcp"
        self.store = store or Store(data_directory() / "remote")

    @contextmanager
    def state(self):
        with self.store.transaction() as root:
            state = root.setdefault(
                "oauth",
                {
                    "origin": self.origin,
                    "clients": {},
                    "pending": {},
                    "codes": {},
                    "access": {},
                    "refresh": {},
                },
            )
            if state["origin"] != self.origin:
                raise ValueError("Origin changed; reset remote connections before reconnecting")
            for collection in ("pending", "codes", "access", "refresh"):
                state[collection] = {
                    k: v for k, v in state[collection].items() if v["expires_at"] > time.time()
                }
            yield state

    async def get_client(self, client_id):
        with self.state() as state:
            value = state["clients"].get(client_id)
            return OAuthClientInformationFull.model_validate(value) if value else None

    async def register_client(self, client_info):
        if (
            not client_info.redirect_uris
            or len(client_info.redirect_uris) > 4
            or not all(valid_callback(uri) for uri in client_info.redirect_uris)
            or client_info.token_endpoint_auth_method
            not in ("none", "client_secret_post", "client_secret_basic")
            or set((client_info.scope or READ_SCOPE).split()) != {READ_SCOPE}
        ):
            raise RegistrationError(
                "invalid_client_metadata", "Use ChatGPT callbacks and whoop:read"
            )
        with self.state() as state:
            if len(state["clients"]) >= 128:
                raise RegistrationError("invalid_client_metadata", "Registration capacity reached")
            state["clients"][client_info.client_id] = client_info.model_dump(mode="json")

    async def authorize(self, client, params):
        if (
            params.resource != self.resource
            or set(params.scopes) != {READ_SCOPE}
            or not params.state
            or len(params.state) > 2048
            or not params.code_challenge
            or not valid_callback(params.redirect_uri)
        ):
            raise AuthorizeError("invalid_request", "Invalid resource, scope, state or callback")
        ticket = secrets.token_urlsafe(32)
        with self.state() as state:
            if len(state["pending"]) >= 32:
                raise AuthorizeError("temporarily_unavailable", "Consent capacity reached")
            state["pending"][ticket] = {
                "client_id": client.client_id,
                "params": params.model_dump(mode="json"),
                "approved": False,
                "expires_at": time.time() + 300,
            }
        return self.origin + "/consent?ticket=" + ticket

    def consent(self, ticket):
        with self.state() as state:
            pending = state["pending"].get(ticket)
            if not pending:
                return HTMLResponse("Connection expired. Start again in ChatGPT.", status_code=400)
            if not pending["approved"]:
                return HTMLResponse(
                    "<h1>WHOOP · Das Kreb</h1><p>Approve access to your WHOOP data in the local terminal.</p><p>Only approve a connection you just started. Paste this command on the computer running the server, review the callback, and type APPROVE.</p><pre>"
                    + html.escape(approval_command(ticket))
                    + '</pre><form action="/consent"><input type="hidden" name="ticket" value="'
                    + html.escape(ticket, quote=True)
                    + '"><button>Continue</button></form>'
                )
            params = AuthorizationParams.model_validate(pending["params"])
            code = secrets.token_urlsafe(32)
            state["codes"][key(code)] = AuthorizationCode(
                code=code,
                client_id=pending["client_id"],
                scopes=params.scopes,
                expires_at=time.time() + 60,
                code_challenge=params.code_challenge,
                redirect_uri=params.redirect_uri,
                redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=self.resource,
                subject="local-owner",
            ).model_dump(mode="json")
            del state["pending"][ticket]
            return RedirectResponse(
                construct_redirect_uri(str(params.redirect_uri), code=code, state=params.state),
                status_code=302,
            )

    def approve(self, ticket):
        if not sys.stdin.isatty():
            raise ValueError("Approval requires your interactive local terminal")
        with self.state() as state:
            pending = state["pending"].get(ticket)
            if not pending:
                raise ValueError("Connection request expired")
            reviewed = dict(pending)
            print("Callback:", pending["params"]["redirect_uri"])
            print("Client:", pending["client_id"])
            print("Scope:", READ_SCOPE)
        if (
            input("Allow this ChatGPT connection to read your WHOOP data? Type APPROVE: ")
            != "APPROVE"
        ):
            raise ValueError("Not approved")
        with self.state() as state:
            if state["pending"].get(ticket) != reviewed:
                raise ValueError("Connection expired or changed during review")
            state["pending"][ticket]["approved"] = True

    async def load_authorization_code(self, client, authorization_code):
        with self.state() as state:
            value = state["codes"].get(key(authorization_code))
            return (
                AuthorizationCode.model_validate(value)
                if value and value["client_id"] == client.client_id
                else None
            )

    def issue(self, state, client_id, family, scopes):
        if len(state["access"]) >= 256 or len(state["refresh"]) >= 128:
            raise TokenError("invalid_grant", "Token capacity reached")
        access, refresh = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        state["access"][key(access)] = AccessToken(
            token=access,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(time.time()) + 3600,
            resource=self.resource,
            subject="local-owner",
            claims={"family": family},
        ).model_dump(mode="json")
        state["refresh"][key(refresh)] = OwnerRefresh(
            token=refresh,
            client_id=client_id,
            scopes=scopes,
            expires_at=int(time.time()) + 30 * 86400,
            resource=self.resource,
            subject="local-owner",
            family=family,
        ).model_dump(mode="json")
        return OAuthToken(
            access_token=access,
            refresh_token=refresh,
            token_type="Bearer",
            expires_in=3600,
            scope=" ".join(scopes),
        )

    async def exchange_authorization_code(self, client, authorization_code):
        with self.state() as state:
            value = state["codes"].pop(key(authorization_code.code), None)
            if (
                not value
                or value["client_id"] != client.client_id
                or value["resource"] != self.resource
            ):
                raise TokenError("invalid_grant", "Code invalid, expired or consumed")
            return self.issue(state, client.client_id, secrets.token_urlsafe(24), value["scopes"])

    async def load_refresh_token(self, client, refresh_token):
        with self.state() as state:
            value = state["refresh"].get(key(refresh_token))
            return (
                OwnerRefresh.model_validate(value)
                if value and value["client_id"] == client.client_id
                else None
            )

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        if set(scopes) != {READ_SCOPE} or refresh_token.resource != self.resource:
            raise TokenError("invalid_scope", "Scope/resource escalation refused")
        with self.state() as state:
            value = state["refresh"].pop(key(refresh_token.token), None)
            if not value or value["client_id"] != client.client_id:
                raise TokenError("invalid_grant", "Refresh token invalid or consumed")
            state["access"] = {
                k: v
                for k, v in state["access"].items()
                if v["claims"]["family"] != refresh_token.family
            }
            return self.issue(state, client.client_id, refresh_token.family, scopes)

    async def load_access_token(self, token):
        with self.state() as state:
            value = state["access"].get(key(token))
            return (
                AccessToken.model_validate(value)
                if value and value["resource"] == self.resource
                else None
            )

    async def revoke_token(self, token):
        family = (
            token.family if isinstance(token, OwnerRefresh) else (token.claims or {}).get("family")
        )
        with self.state() as state:
            state["access"] = {
                k: v for k, v in state["access"].items() if v["claims"]["family"] != family
            }
            state["refresh"] = {k: v for k, v in state["refresh"].items() if v["family"] != family}


class Boundary:
    def __init__(self, app, origin, port):
        self.app, self.origin = app, origin
        self.hosts = {urlsplit(origin).netloc, f"127.0.0.1:{port}", f"localhost:{port}"}
        self.window, self.count = time.monotonic(), 0

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        if (
            headers.get("host") not in self.hosts
            or headers.get("origin", self.origin) != self.origin
        ):
            return await JSONResponse({"error": "Invalid host or origin"}, status_code=403)(
                scope, receive, send
            )
        if time.monotonic() - self.window >= 60:
            self.window, self.count = time.monotonic(), 0
        self.count += 1
        if self.count > 120:
            return await JSONResponse({"error": "Rate limit exceeded"}, status_code=429)(
                scope, receive, send
            )
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > (1024 * 1024 if scope["path"] == "/mcp" else 16384):
                return await JSONResponse({"error": "Request too large"}, status_code=413)(
                    scope, receive, send
                )
            if not message.get("more_body", False):
                break
        if scope["path"] in ("/token", "/revoke"):
            form = parse_qs(body.decode("utf-8", errors="replace"), keep_blank_values=True)
            if "resource" in form and form["resource"] != [self.origin + "/mcp"]:
                return await JSONResponse({"error": "invalid_target"}, status_code=400)(
                    scope, receive, send
                )
            if scope["path"] == "/revoke" and "client_secret" not in form:
                body.extend(b"&client_secret=")
        delivered = False

        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        async def secure_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"cache-control", b"no-store"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-content-type-options", b"nosniff"),
                    (
                        b"content-security-policy",
                        b"default-src 'none'; form-action 'self'; frame-ancestors 'none'",
                    ),
                ]
            await send(message)

        await self.app(scope, replay, secure_send)


def create_http_app(origin, port=8788, store=None, client=None):
    provider = OwnerProvider(origin, store)
    auth = AuthSettings(
        issuer_url=AnyHttpUrl(provider.origin),
        resource_server_url=AnyHttpUrl(provider.resource),
        validate_token_resource=True,
        required_scopes=[READ_SCOPE],
        client_registration_options=ClientRegistrationOptions(
            enabled=True, valid_scopes=[READ_SCOPE], default_scopes=[READ_SCOPE]
        ),
        revocation_options=RevocationOptions(enabled=True),
    )
    server = create_server(
        client,
        host="127.0.0.1",
        port=port,
        auth=auth,
        auth_server_provider=provider,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=[urlsplit(origin).netloc, f"127.0.0.1:{port}", f"localhost:{port}"],
            allowed_origins=[origin],
        ),
    )

    @server.custom_route("/consent", methods=["GET"])
    async def consent(request):
        return provider.consent(request.query_params.get("ticket", ""))

    @server.custom_route("/health", methods=["GET"])
    async def health(request):
        return JSONResponse({"status": "ready", "authentication": "oauth", "read_only": True})

    return Boundary(server.streamable_http_app(), provider.origin, port), provider


def run(args):
    store = Store(data_directory() / "remote")
    if args.action == "reset":
        if (
            not sys.stdin.isatty()
            or input("Revoke all remote connections? Type RESET: ") != "RESET"
        ):
            raise ValueError("Not reset")
        with store.transaction() as state:
            state.clear()
        print("All remote grants revoked; local WHOOP login preserved.")
        return
    origin = args.public_url
    if not origin:
        with store.transaction() as state:
            origin = state.get("oauth", {}).get("origin")
    if not origin:
        raise ValueError("Provide --public-url https://your-host")
    if args.action == "approve":
        OwnerProvider(origin, store).approve(args.ticket)
        print("Approved. Return to ChatGPT and select Continue.")
    else:
        if not 1024 <= args.port <= 65535:
            raise ValueError("Use an unprivileged port")
        import uvicorn

        app, _ = create_http_app(origin, args.port, store)
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=args.port,
            access_log=False,
            log_level="warning",
            proxy_headers=False,
            limit_concurrency=16,
            timeout_keep_alive=5,
        )
