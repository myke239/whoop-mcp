"""Build on the target OS; never imply a cross-compiled or signed executable."""

import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.environ["PYINSTALLER_CONFIG_DIR"] = str(root / "work" / "pyinstaller")
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "whoop-mcp",
        "--collect-all",
        "whoop_mcp",
        "--collect-all",
        "keyring",
        "--copy-metadata",
        "whoop-mcp-das-kreb",
        "--add-data",
        str(root / "plugins" / "whoop") + ":whoop_mcp/bundled_plugin",
        str(root / "scripts" / "frozen_entry.py"),
    ],
    cwd=root,
    check=True,
)
