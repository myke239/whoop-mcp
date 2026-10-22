"""Keep process-owned stdio handles open through frozen executable shutdown."""

import sys

import anyio
from mcp.server.stdio import stdio_server


def run(server):
    # The SDK's default TextIOWrapper takes ownership of the underlying handle.
    # Its finalizer can close stdout before the frozen bootloader flushes it.
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8")

    async def serve():
        async with stdio_server(
            stdin=anyio.wrap_file(sys.stdin), stdout=anyio.wrap_file(sys.stdout)
        ) as (read, write):
            await server._mcp_server.run(
                read, write, server._mcp_server.create_initialization_options()
            )

    anyio.run(serve)
