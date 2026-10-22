# Security and privacy

Report a suspected vulnerability through GitHub private vulnerability reporting at
https://github.com/myke239/whoop-mcp/security/advisories/new.
Do not post access tokens, OAuth callbacks, client secrets or health data in public issues.

Supported version: latest 0.1.x release. This self-hosted server serves a single owner.
The owner controls the machine, operating-system keyring and trusted HTTPS forwarding.
The MCP client receives the requested health data; do not connect untrusted clients.

Secrets are encrypted with a Fernet key stored in the OS keyring: Windows Credential
Manager, macOS Keychain or Linux Secret Service. Unsupported or locked keyrings fail
closed. Unix directories are owner-only. The Windows OS keyring protects the key;
encrypted application files still require normal user-profile filesystem protection.

Remote access uses OAuth authorization-code flow with S256 PKCE, a local terminal
consent step, a fixed read scope, resource binding, short-lived access tokens, rotated
refresh tokens and revocation. The WHOOP upstream token is never used as an MCP token.
Remote client registrations allow only documented ChatGPT callback patterns.

Response and request sizes, pagination, registration count, token count, request rate
and HTTP concurrency are bounded. No automatic account writes or retries after uncertain
upstream responses. Logs omit response bodies and OAuth callback request paths.

Stopping the public forwarding service disables remote reachability. `remote reset`
revokes all remote grants. `logout` removes the local WHOOP session; revoke the app in
WHOOP settings to withdraw the upstream grant. Uninstall preserves credentials.
