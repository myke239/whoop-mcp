import json
import os
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from whoop_mcp.server import create_server


async def test_discovery_and_guide():
    server = create_server()
    tools = await server.list_tools()
    assert len(tools) == 15
    assert all(t.annotations.readOnlyHint and not t.annotations.destructiveHint for t in tools)
    content = await server.call_tool("get_whoop_guide", {})
    result = json.loads(content[0].text)
    assert result["author"] == "Das Kreb"


async def test_real_stdio_initialize_and_call(tmp_path):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "whoop_mcp.cli", "serve"],
        env={**os.environ, "WHOOP_MCP_DATA_DIR": str(tmp_path)},
    )
    async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        assert len(tools.tools) == 15
        result = await session.call_tool("get_whoop_guide", {})
        assert not result.isError
        assert "Das Kreb" in result.content[0].text


def test_stdio_eof_keeps_bootloader_handles_open():
    process = subprocess.Popen(
        [sys.executable, "-m", "whoop_mcp.cli", "serve"],
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
                    "clientInfo": {"name": "eof-test", "version": "1"},
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
