"""WHOOP authorization-code login and serialized refresh-token rotation."""

import secrets
import time
from urllib.parse import parse_qs, urlencode, urlsplit

import httpx

from .storage import Store
from .tls import context

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
SCOPES = (
    "read:recovery",
    "read:cycles",
    "read:workout",
    "read:sleep",
    "read:profile",
    "read:body_measurement",
    "offline",
)


class WhoopError(Exception):
    """Only a stable, non-sensitive code may cross the MCP boundary."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def redirect_uri(value):
    parts = urlsplit(value)
    if (
        parts.scheme != "http"
        or parts.hostname != "127.0.0.1"
        or not parts.port
        or not 1024 <= parts.port <= 65535
        or parts.path != "/callback"
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
    ):
        raise ValueError("Use http://127.0.0.1:<unprivileged-port>/callback")
    return value


class Auth:
    def __init__(self, store=None, client=None):
        self.store = store or Store()
        self.client = client or httpx.Client(timeout=30, follow_redirects=False, verify=context())

    def configure(self, client_id, client_secret, callback):
        if not client_id.strip() or not client_secret.strip():
            raise ValueError("Client ID and secret are required")
        with self.store.transaction() as state:
            state.clear()
            state["config"] = {
                "client_id": client_id.strip(),
                "client_secret": client_secret,
                "redirect_uri": redirect_uri(callback),
            }

    def begin(self):
        nonce = secrets.token_urlsafe(32)
        with self.store.transaction() as state:
            config = state.get("config")
            if not config:
                raise WhoopError("SETUP_REQUIRED")
            state["login"] = {"state": nonce, "expires_at": time.time() + 300}
        return (
            AUTH_URL
            + "?"
            + urlencode(
                {
                    "response_type": "code",
                    "client_id": config["client_id"],
                    "redirect_uri": config["redirect_uri"],
                    "scope": " ".join(SCOPES),
                    "state": nonce,
                }
            )
        )

    def complete(self, callback_url):
        parts = urlsplit(callback_url)
        query = parse_qs(parts.query, keep_blank_values=True)
        with self.store.transaction() as state:
            login = state.get("login", {})
            config = state.get("config", {})
            expected = urlsplit(config.get("redirect_uri", ""))
            if (
                (parts.scheme, parts.netloc, parts.path)
                != (expected.scheme, expected.netloc, expected.path)
                or parts.fragment
                or not {"code", "state"} <= set(query)
                or not set(query) <= {"code", "state", "scope"}
                or any(len(v) != 1 for v in query.values())
                or not query.get("code", [""])[0]
                # WHOOP includes the granted scope in successful redirects. It is
                # informational here; only the token exchange establishes access.
                or (
                    "scope" in query
                    and (
                        not query["scope"][0].split()
                        or not set(query["scope"][0].split()) <= set(SCOPES)
                    )
                )
                or login.get("expires_at", 0) < time.time()
                or not secrets.compare_digest(query.get("state", [""])[0], login.get("state", "!"))
            ):
                raise WhoopError("INVALID_CALLBACK")
            token = self._exchange(
                {"grant_type": "authorization_code", **config, "code": query["code"][0]}
            )
            state["token"] = token
            state.pop("login", None)

    def _exchange(self, data):
        try:
            response = self.client.post(TOKEN_URL, data=data)
            if response.status_code != 200:
                raise WhoopError("AUTH_REQUIRED")
            token = response.json()
            if (
                not isinstance(token.get("access_token"), str)
                or not token["access_token"]
                or not isinstance(token.get("refresh_token"), str)
                or not token["refresh_token"]
                or token.get("token_type", "").lower() != "bearer"
                or not 0 < float(token["expires_in"]) <= 365 * 86400
            ):
                raise WhoopError("INVALID_TOKEN_RESPONSE")
            token["expires_at"] = time.time() + float(token["expires_in"])
            return token
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise WhoopError("AUTH_SERVICE_ERROR") from None

    def access_token(self):
        with self.store.transaction() as state:
            token = state.get("token")
            if not token:
                raise WhoopError("AUTH_REQUIRED")
            if token["expires_at"] <= time.time() + 60:
                config = state.get("config", {})
                token = self._exchange(
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": token["refresh_token"],
                        "client_id": config["client_id"],
                        "client_secret": config["client_secret"],
                    }
                )
                state["token"] = token
            return token["access_token"]

    def logout(self):
        with self.store.transaction() as state:
            state.pop("token", None)
            state.pop("login", None)
