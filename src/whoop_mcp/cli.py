"""Interactive setup stays on the owner's machine; serve keeps stdout MCP-only."""

import argparse
import getpass
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

from . import __version__
from .auth import Auth, WhoopError


def interactive():
    if not sys.stdin.isatty():
        raise ValueError("Run this command in your interactive local terminal")


def login(auth):
    interactive()
    with auth.store.transaction() as state:
        callback = state.get("config", {}).get("redirect_uri")
    if not callback:
        raise WhoopError("SETUP_REQUIRED")
    url = auth.begin()
    outcome = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if urlsplit(self.path).path != "/callback":
                self.send_error(404)
                return
            try:
                auth.complete(callback + "?" + urlsplit(self.path).query)
                message = b"Connected to WHOOP. You may close this tab."
                outcome.append(True)
                self.send_response(200)
            except WhoopError:
                message = b"Authorization failed. Return to the terminal and retry."
                self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

        def log_message(self, *_):
            pass  # Callback URLs contain authorization codes.

    import time

    with HTTPServer(("127.0.0.1", urlsplit(callback).port), Handler) as server:
        server.timeout = 1
        print("Authorize WHOOP in your browser. This request expires in five minutes.")
        print(url)
        webbrowser.open(url)
        deadline = time.monotonic() + 300
        while not outcome and time.monotonic() < deadline:
            server.handle_request()
    if not outcome:
        raise WhoopError("LOGIN_EXPIRED")
    print("Connected. Run whoop-mcp verify.")


def main():
    parser = argparse.ArgumentParser(description="WHOOP MCP by Das Kreb")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("serve", "setup", "login", "verify", "doctor", "logout", "install-plugin"):
        sub.add_parser(name)
    remote = sub.add_parser("remote")
    remote.add_argument("action", choices=["serve", "approve", "reset"])
    remote.add_argument("ticket", nargs="?")
    remote.add_argument("--public-url")
    remote.add_argument("--port", type=int, default=8788)
    tunnel = sub.add_parser("tunnel")
    tunnel.add_argument("action", choices=["setup", "run", "status"])
    tunnel.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    try:
        if args.command == "serve":
            from .server import create_server
            from .stdio import run

            run(create_server())
        elif args.command == "remote":
            from .remote import run

            run(args)
        elif args.command == "tunnel":
            from .tunnel import run

            run(args)
        elif args.command == "install-plugin":
            from .plugin import install

            print(install())
        elif args.command == "setup":
            interactive()
            print(
                "Create an app at https://developer.whoop.com and register the exact callback below."
            )
            callback = (
                input("Callback [http://127.0.0.1:8937/callback]: ").strip()
                or "http://127.0.0.1:8937/callback"
            )
            Auth().configure(
                input("WHOOP client ID: ").strip(),
                getpass.getpass("WHOOP client secret: "),
                callback,
            )
            print("Encrypted configuration saved. Run whoop-mcp login.")
        elif args.command == "login":
            login(Auth())
        elif args.command == "verify":
            from .client import WhoopClient

            WhoopClient().singleton("body")
            print("WHOOP authenticated read passed. No measurements were printed.")
        elif args.command == "logout":
            interactive()
            Auth().logout()
            print(
                "Local WHOOP session removed. Remote grants are separate; run remote reset to revoke them."
            )
        elif args.command == "doctor":
            from .storage import Store, data_directory

            store = Store()
            with store.transaction() as state:
                result = {
                    "version": __version__,
                    "python": sys.version.split()[0],
                    "data_directory": str(data_directory()),
                    "configured": bool(state.get("config")),
                    "logged_in": bool(state.get("token")),
                    "encrypted_storage": True,
                }
            print(json.dumps(result, indent=2))
    except WhoopError as error:
        print("WHOOP: " + error.code, file=sys.stderr)
        raise SystemExit(1) from None
    except (ValueError, RuntimeError, OSError) as error:
        # These errors describe local configuration only; HTTP errors are sanitized upstream.
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
