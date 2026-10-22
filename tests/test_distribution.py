import json
import sys
from pathlib import Path

from whoop_mcp.plugin import install
from whoop_mcp.remote import approval_command


def test_plugin_absolute_command_and_guided_skills(tmp_path):
    install(tmp_path / "plugin")
    root = tmp_path / "plugin"
    manifest = json.loads((root / ".codex-plugin/plugin.json").read_text())
    assert manifest["author"]["name"] == "Das Kreb"
    assert manifest["version"] == "0.1.0"
    server = json.loads((root / ".mcp.json").read_text())["mcpServers"]["whoop"]
    assert Path(server["command"]).is_absolute()
    assert server["args"] == ["-m", "whoop_mcp.cli", "serve"]
    assert len(list((root / "skills").glob("*/SKILL.md"))) == 3


def test_frozen_commands_do_not_invoke_python_module(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    install(tmp_path / "plugin")
    server = json.loads((tmp_path / "plugin/.mcp.json").read_text())["mcpServers"]["whoop"]
    assert server["args"] == ["serve"]
    assert "whoop_mcp.cli" not in approval_command("ticket")
