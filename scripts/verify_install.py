"""Exercise the managed installer in a clean prefix and real installed MCP process."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

root = Path(__file__).resolve().parents[1]
prefix = root / "work" / "installed-smoke-v2"
subprocess.run(
    [sys.executable, str(root / "scripts" / "install.py"), "--prefix", str(prefix)], check=True
)
receipt = json.loads((prefix / "installation.json").read_text())
launcher = receipt["launcher"]


async def verify():
    params = StdioServerParameters(
        command=launcher,
        args=["serve"],
        env={**os.environ, "WHOOP_MCP_DATA_DIR": str(root / "work" / "installed-smoke-data")},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        assert len(tools.tools) == 15
        result = await session.call_tool("get_whoop_guide", {})
        assert not result.isError
        assert "Das Kreb" in result.content[0].text


asyncio.run(verify())
subprocess.run(
    [launcher, "install-plugin"],
    check=True,
    env={**os.environ, "CODEX_HOME": str(root / "work" / "installed-smoke-codex")},
)
plugin = json.loads((root / "work/installed-smoke-codex/plugins/local/whoop/.mcp.json").read_text())
assert Path(plugin["mcpServers"]["whoop"]["command"]).is_absolute()
print("Installed wheel, plugin copy and real stdio MCP verified.")
