WHOOP MCP by **Das Kreb** brings official WHOOP recovery, sleep, cycles and workout data to MCP assistants.

Includes 15 read tools, three guided plugin skills, encrypted local OAuth storage,
personal remote HTTP with OAuth/PKCE, and managed installers for Windows/macOS/Linux.

Native archives include a Python runtime. They are unsigned. Compare the adjacent
SHA-256 manifest after downloading. Install the Codex plugin using `install-plugin`.
Source-based managed installers require Python 3.12+.

Read [installation](https://github.com/myke239/whoop-mcp/blob/main/docs/installation.md),
[remote setup](https://github.com/myke239/whoop-mcp/blob/main/docs/chatgpt.md) and
[verification evidence](https://github.com/myke239/whoop-mcp/blob/main/docs/verification.md).

Version 0.1.1 fixes the OAuth callback scope rejection and handles missing optional
body measurements during verification. Live WHOOP authorization and empty-account MCP
reads passed. Populated-record acceptance, ChatGPT connection and phone availability
still require separate verification. Shared-host OAuth is available at `/mcp/whoop/`;
the offline suite contains 66 tests.
WHOOP's public member API does not expose workout creation, scheduling or journal edits.
Independent project; not affiliated with WHOOP or OpenAI.

**Windows download limitation:** the downloaded unsigned executable was terminated by
Avast's sandbox on the owner's machine and returned Access is denied. Windows CI and
the locally built executable passed, but the downloaded-binary check did not. Use the
tested managed Python installer for account testing. No security protection was disabled.
This release remains a prerelease pending populated-data/ChatGPT acceptance and native download trust.
