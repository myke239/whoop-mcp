"""Create named archives and SHA-256 manifests for native releases."""

import hashlib
import platform
import shutil
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "dist/release"
out.mkdir(parents=True, exist_ok=True)
name = f"whoop-mcp-0.1.0-{platform.system().lower()}-{platform.machine().lower()}"
archive = Path(shutil.make_archive(str(out / name), "zip", root / "dist", "whoop-mcp"))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(out / (name + ".sha256")).write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
for wheel in (root / "dist").glob("*.whl"):
    shutil.copy2(wheel, out / wheel.name)
inventory = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
(out / (name + "-dependencies.txt")).write_text(inventory, encoding="utf-8")
