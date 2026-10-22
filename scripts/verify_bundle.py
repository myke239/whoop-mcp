"""Verify native bundle without WHOOP account access."""

import asyncio
import os
import subprocess
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = Path(__file__).resolve().parents[1]
launcher = root / "dist/whoop-mcp" / ("whoop-mcp.exe" if os.name == "nt" else "whoop-mcp")
subprocess.run([str(launcher), "--version"], check=True)


async def verify():
    async with (
        stdio_client(StdioServerParameters(command=str(launcher), args=["serve"])) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        assert len((await session.list_tools()).tools) == 15
        assert not (await session.call_tool("get_whoop_guide", {})).isError


asyncio.run(verify())
subprocess.run(
    [str(launcher), "install-plugin"],
    check=True,
    env={**os.environ, "CODEX_HOME": str(root / "work" / "frozen-smoke-codex")},
)
print("Native bundle version, stdio MCP and plugin copy verified.")
