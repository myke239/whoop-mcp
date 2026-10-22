"""Isolate CI from packages preinstalled on hosted runners."""

import os
import sys
import venv
from pathlib import Path

root = Path(__file__).resolve().parents[1] / ".venv"
venv.EnvBuilder(with_pip=True).create(root)
with Path(os.environ["GITHUB_PATH"]).open("a", encoding="utf-8") as stream:
    stream.write(str(root / ("Scripts" if sys.platform == "win32" else "bin")) + "\n")
with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as stream:
    stream.write("VIRTUAL_ENV=" + str(root) + "\n")
