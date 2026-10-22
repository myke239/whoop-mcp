"""Cross-platform managed installer. Run from a downloaded/extracted release."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path
from urllib.request import urlopen


def default_root():
    if sys.platform == "win32":
        return Path(os.environ["LOCALAPPDATA"]) / "Programs" / "WhoopMCP"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "WhoopMCP"
    return (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        / "whoop-mcp"
        / "application"
    )


def main():
    parser = argparse.ArgumentParser(description="Install WHOOP MCP by Das Kreb")
    parser.add_argument("--prefix", type=Path)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--plugin", action="store_true")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    root = (args.prefix or default_root()).absolute()
    if root.is_symlink() or root == Path(root.anchor) or len(root.parts) < 3:
        raise SystemExit("Refusing unsafe installation prefix")
    receipt = root / "installation.json"
    if args.uninstall:
        if not receipt.is_file() or json.loads(receipt.read_text())["product"] != "whoop-mcp":
            raise SystemExit("No WHOOP installation receipt at this prefix")
        if (
            input(f"Remove application at {root}? Credentials are preserved. Type REMOVE: ")
            != "REMOVE"
        ):
            raise SystemExit("Not removed")
        shutil.rmtree(root)
        return
    if sys.version_info < (3, 12):  # noqa: UP036 -- installer may run before package requirements are checked
        raise SystemExit("Python 3.12+ is required. Install it from python.org and retry.")
    if root.exists() and any(root.iterdir()) and not receipt.is_file():
        raise SystemExit("Prefix is not empty and has no WHOOP installation receipt")
    root.mkdir(parents=True, exist_ok=True)
    receipt.write_text(
        json.dumps({"product": "whoop-mcp", "status": "installing", "root": str(root)}),
        encoding="utf-8",
    )
    runtime = root / "runtime"
    venv.EnvBuilder(with_pip=True).create(runtime)
    python = runtime / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip>=26.2"], check=True)
    # Retrieve pinned MCP through PyPI's version API. This avoids a large simple-index
    # response that some HTTPS inspection proxies frame incorrectly; TLS stays enabled.
    with urlopen("https://pypi.org/pypi/mcp/1.30.0/json", timeout=30) as response:
        metadata = json.load(response)
    wheel_info = next(
        item for item in metadata["urls"] if item["filename"].endswith("-py3-none-any.whl")
    )
    if not wheel_info["url"].startswith("https://files.pythonhosted.org/"):
        raise SystemExit("Unexpected MCP distribution host")
    dependency = wheel_info["url"] + "#sha256=" + wheel_info["digests"]["sha256"]
    subprocess.run([str(python), "-m", "pip", "install", dependency], check=True)
    source = Path(__file__).resolve().parents[1]
    wheel = args.wheel
    if wheel is None:
        wheels = list((source / "dist").glob("whoop_mcp_das_kreb-*.whl"))
        wheel = wheels[0] if len(wheels) == 1 else None
    target = str(wheel.resolve()) + "[remote]" if wheel else str(source) + "[remote]"
    subprocess.run([str(python), "-m", "pip", "install", target], check=True)
    launcher = runtime / ("Scripts/whoop-mcp.exe" if os.name == "nt" else "bin/whoop-mcp")
    subprocess.run([str(launcher), "--version"], check=True)
    receipt.write_text(
        json.dumps(
            {
                "product": "whoop-mcp",
                "root": str(root),
                "python": str(python),
                "launcher": str(launcher),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if args.plugin:
        subprocess.run([str(launcher), "install-plugin"], check=True)
    print(f"Installed. Run:\n  {launcher} setup\n  {launcher} login\n  {launcher} verify")


if __name__ == "__main__":
    main()
