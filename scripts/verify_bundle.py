"""Verify native bundle without WHOOP account access."""

import asyncio
import json
import os
import subprocess
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = Path(__file__).resolve().parents[1]
launcher = root / "dist/whoop-mcp" / ("whoop-mcp.exe" if os.name == "nt" else "whoop-mcp")
subprocess.run([str(launcher), "--version"], check=True)
# Verify graceful EOF shutdown too; a zero bootloader exit alone can hide Python stderr.
process = subprocess.Popen(
    [str(launcher), "serve"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
)
process.stdin.write(
    json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "bundle-smoke", "version": "1"},
            },
        }
    )
    + "\n"
)
process.stdin.flush()
assert "result" in json.loads(process.stdout.readline())
process.stdin.close()
process.wait(timeout=30)
assert process.returncode == 0
assert "Traceback" not in process.stderr.read()


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
