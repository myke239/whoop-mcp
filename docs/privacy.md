# Privacy policy

WHOOP MCP is an independent, self-hosted tool by Das Kreb. It has no vendor-operated
data collection endpoint, advertising, analytics or telemetry. Its public GitHub Pages
site is documentation only and does not accept account credentials or health records.
GitHub may process normal website traffic according to its own privacy policy.
The website uses Google Fonts; Google receives font requests from visitors' browsers.

After your consent, the server reads WHOOP profile, body measurements, cycles, recovery,
sleep and workouts. It returns requested information to your chosen MCP client; that
client's provider handles the resulting conversation under its own terms. A tunnel or
hosting provider may also process traffic when you enable remote access.

OAuth client configuration and tokens are encrypted locally using an OS-keyring-managed
key. Remote OAuth grants are stored separately in encrypted local state. Health records
are processed in memory and are not persistently archived by this server. Name, email
and member IDs are omitted from ordinary training responses; the explicit profile tool
returns identity fields. No location-track endpoint is exposed.

You control retention: `logout` removes local WHOOP tokens; `remote reset` removes remote
registrations and grants. Revoke the developer app in WHOOP to withdraw upstream access.
Uninstall intentionally preserves the private state directory, so remove it separately
only after revoking access if you want complete local deletion. OS-keyring entries must
also be removed through your OS credential manager if no longer needed.

For project questions or data-handling issues, use
[GitHub issues](https://github.com/myke239/whoop-mcp/issues) without personal data.
Security concerns belong in private vulnerability reporting, linked from SECURITY.md.

Effective 2026-10-22. This policy describes this software; a third-party deployment
must supply its own operator identity and processing terms.
