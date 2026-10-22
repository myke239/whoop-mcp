"""Install a bundled plugin with an absolute interpreter path."""

import json
import os
import shutil
import sys
from importlib.resources import files
from pathlib import Path


def install(destination=None):
    root = (
        Path(destination)
        if destination
        else Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
        / "plugins"
        / "local"
        / "whoop"
    )
    if root.is_symlink():
        raise ValueError("Plugin destination must not be a link")
    source = files("whoop_mcp").joinpath("bundled_plugin")
    # Editable installs read the same version-controlled plugin.
    if not source.is_dir():
        source = Path(__file__).resolve().parents[2] / "plugins" / "whoop"
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(source), root, dirs_exist_ok=True)
    command = [sys.executable, "-m", "whoop_mcp.cli", "serve"]
    if getattr(sys, "frozen", False):
        command = [sys.executable, "serve"]
    (root / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "whoop": {
                        "command": command[0],
                        "args": command[1:],
                        "startup_timeout_sec": 30,
                        "tool_timeout_sec": 240,
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return (
        f"Plugin copied to {root}. Add this local plugin in Codex plugin settings, then start a new chat. "
        "Alternatively add https://github.com/myke239/whoop-mcp as a plugin marketplace."
    )
