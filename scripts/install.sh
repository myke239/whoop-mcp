#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Install Python 3.12+ from python.org or your package manager, then retry.' >&2
  exit 1
fi
exec python3 "$SCRIPT_DIR/install.py" "$@"
