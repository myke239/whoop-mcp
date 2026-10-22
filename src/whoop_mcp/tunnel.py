"""Personal ngrok forwarding with encrypted token storage and a reserved loopback port."""

import getpass
import os
import socket
import sys

from .remote import create_http_app
from .storage import Store, data_directory


def reserve(port):
    if not 1024 <= port <= 65535:
        raise ValueError("Use an unprivileged loopback port")
    sock = socket.socket()
    try:
        if sys.platform == "win32":
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(128)
        return sock
    except OSError:
        sock.close()
        raise ValueError(
            "Loopback port is occupied or unavailable; stop the old server or choose another port"
        ) from None


def run(args):
    store = Store(data_directory() / "tunnel")
    if args.action == "setup":
        if not sys.stdin.isatty():
            raise ValueError("Run tunnel setup in your own interactive local terminal")
        token = getpass.getpass("ngrok authtoken (hidden): ").strip()
        if not token or any(c.isspace() for c in token):
            raise ValueError("Expected a single ngrok authtoken")
        with store.transaction() as state:
            state["authtoken"] = token
        print("Tunnel token saved in encrypted local storage.")
        return
    with store.transaction() as state:
        if args.action == "status":
            value = state.get("status")
            print(value or "No active foreground tunnel recorded.")
            return
        token = state.get("authtoken")
    if not token:
        raise ValueError("Run whoop-mcp tunnel setup first")
    import ngrok
    import uvicorn

    sock = reserve(args.port)
    listener = None
    try:
        listener = ngrok.forward(f"http://127.0.0.1:{args.port}", authtoken=token)
        origin = listener.url()
        app, provider = create_http_app(origin, args.port)
        with provider.state():
            pass  # Refuse a changed public origin before serving an old grant store.
        with store.transaction() as state:
            state["status"] = {"url": origin + "/mcp", "pid": os.getpid(), "port": args.port}
        print("Authenticated WHOOP MCP: " + origin + "/mcp", flush=True)
        config = uvicorn.Config(
            app,
            access_log=False,
            log_level="warning",
            proxy_headers=False,
            timeout_keep_alive=5,
            limit_concurrency=16,
        )
        uvicorn.Server(config).run(sockets=[sock])
    except Exception:
        # SDK exceptions can contain account or forwarding details. No secrets on stderr.
        raise RuntimeError(
            "Tunnel stopped or could not start. Check your local ngrok account, network and saved public origin."
        ) from None
    finally:
        if listener is not None:
            ngrok.disconnect(listener.url())
        sock.close()
        with store.transaction() as state:
            state.pop("status", None)
