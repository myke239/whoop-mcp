# Install WHOOP MCP

By **Das Kreb**. Use the [public releases](https://github.com/myke239/whoop-mcp/releases).
These are per-user installers; no administrator access is required. Managed installers
require Python 3.12+ and internet access for dependencies. Native bundles, when attached
to a release, include Python. Executables are unsigned unless a release explicitly says otherwise.

Download a source archive or clone the repository. Review the installer before running it.

Windows PowerShell:

```powershell
git clone https://github.com/myke239/whoop-mcp.git
cd whoop-mcp
./scripts/install.ps1 -Plugin
```

macOS or Linux:

```sh
git clone https://github.com/myke239/whoop-mcp.git
cd whoop-mcp
sh scripts/install.sh --plugin
```

Use `--prefix /absolute/path` with the Python/shell installer or `-Prefix D:\path` on Windows.
Defaults: `%LOCALAPPDATA%\Programs\WhoopMCP` on Windows,
`~/Library/Application Support/WhoopMCP` on macOS, and
`${XDG_DATA_HOME:-~/.local/share}/whoop-mcp/application` on Linux.
The installer prints the absolute launcher. It does not change PATH or install a background service.

Run that launcher with `setup`, then `login`, then `verify`. In PowerShell, prefix a quoted
launcher path with `&`. On macOS/Linux, execute the quoted path directly.

## WHOOP OAuth setup

Create an application in the [WHOOP developer dashboard](https://developer.whoop.com/).
Register the exact redirect URI `http://127.0.0.1:8937/callback` (or your chosen unprivileged
loopback port). Complete the app's required metadata, including privacy policy and website.
The local `setup` command prompts for your client ID, hidden client secret and callback;
encrypted configuration is stored locally. Never send those values to an assistant.

`login` opens WHOOP's consent page and listens on the registered loopback callback for
five minutes. Requested scopes: `read:cycles`, `read:recovery`, `read:sleep`, `read:workout`,
`read:profile`, `read:body_measurement` and `offline` for refresh.
WHOOP approval/developer-account restrictions may apply to your application.
`verify` performs an authenticated profile read without printing profile fields. Body
measurements may be unavailable even when login works; a 404 from that tool is reported
as unavailable data rather than an authentication failure.

Windows uses Credential Manager; macOS uses Keychain. Linux requires an unlocked Secret
Service keyring (such as GNOME Keyring). Headless Linux needs a working secret-service
session; plaintext fallback is intentionally unavailable.

## Develop locally

```sh
python -m venv .venv
# Use .venv/Scripts/python.exe on Windows, .venv/bin/python on macOS/Linux:
.venv/bin/python -m pip install -e '.[dev,remote]'
.venv/bin/whoop-mcp setup
.venv/bin/whoop-mcp login
.venv/bin/whoop-mcp verify
```

## Update and remove

Stop all running WHOOP server processes, then rerun the installer from the new release.
Existing encrypted credentials are separate from the application runtime and preserved.
Use `scripts/install.py --uninstall --prefix <installed-root>` to remove a managed
installation after an interactive confirmation. Remove an installed local plugin from
Codex separately. To revoke access first, run `remote reset`, `logout`, and revoke the
developer application in your WHOOP account settings.
