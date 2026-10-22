# Troubleshooting

Run `whoop-mcp doctor` in your terminal for redacted setup status. It never prints tokens
or health records. `verify` checks a real authenticated read without printing measurements.

| Code / symptom | Next step |
| --- | --- |
| SETUP_REQUIRED | Run setup with a WHOOP developer application |
| AUTH_REQUIRED | Run login; check that the developer grant is still active |
| SCOPE_REQUIRED | Reauthorize with the required member read scopes |
| INVALID_CALLBACK | Check exact loopback URI, state, expiry and duplicated query fields |
| RATE_LIMITED | Wait before retrying; reduce repeated broad history requests |
| NETWORK_ERROR / UPSTREAM_ERROR | Check connectivity and WHOOP status; do not disable TLS checks |
| RESPONSE_TOO_LARGE / INVALID_RESPONSE | Reduce the query; report a redacted reproduction |
| PAGINATION_LOOP | Upstream repeated a token; retry later and report the stable code |
| LOCAL_SERVICE_ERROR | Run doctor locally; unlock the OS keyring |
| Keyring unavailable on Linux | Start/unlock a Secret Service session; plaintext fallback is unavailable |
| ChatGPT returns 401 | Reconnect OAuth; confirm the resource matches the public origin + /mcp |
| Origin changed | Stop server, run remote reset, then reconnect at the new origin |
| No plugin tools in Codex | Check the absolute launcher, plugin enabled state, and start a new chat |
| Downloaded Windows executable returns Access is denied | The owner's Avast sandbox terminated the unsigned prerelease executable. Use the tested managed Python installer; do not disable antivirus or TLS protections. Native download acceptance remains unresolved. |

Package installation requires Python 3.12+. An installed interpreter can be selected
explicitly: `path/to/python scripts/install.py`. On Windows `py -3.13` can select Python 3.13.
Do not upload state.enc, OS credentials, OAuth callback URLs or health responses to issues.
