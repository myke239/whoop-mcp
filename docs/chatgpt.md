# Personal ChatGPT connection

The server supports authenticated Streamable HTTP at `/mcp`. This is a self-hosted,
single-owner connection. It is not a hosted public service or an approved marketplace
listing. Your machine and HTTPS forwarding service must remain running.

1. Complete local `setup`, `login` and `verify`.
2. Forward a stable public HTTPS origin to `http://127.0.0.1:8788` using a trusted reverse
   proxy or tunnel provider. The forwarding service can see health-data responses.
   Configure that provider locally; never paste tunnel tokens in chat.
3. Run the installed launcher:

   ```sh
   whoop-mcp remote serve --public-url https://your-host.example --port 8788
   ```

4. In ChatGPT's plugin/custom MCP setup on the web, enter `https://your-host.example/mcp`.
   Choose OAuth and Dynamic Client Registration (DCR), with scope `whoop:read`. Leave
   static client ID and secret blank. Names and availability depend on your account.
5. The consent page displays a command. Run it on the server machine, inspect the
   ChatGPT callback and client ID, then type `APPROVE`. Return to the page and Continue.
   Consent expires after five minutes.
6. Test `get_whoop_guide`, then a bounded authenticated query in a new ChatGPT chat.
   Check the same connection on your phone. Mobile availability requires verification
   on your account; server compatibility alone does not establish phone support.

## Guided ngrok alternative

The remote extra includes the ngrok SDK. If you use ngrok, run `whoop-mcp tunnel setup`
locally and enter its authtoken at the hidden prompt. Then run `whoop-mcp tunnel run`.
It reserves the loopback socket before opening the tunnel and prints the public MCP URL.
Use that URL in ChatGPT and follow the same OAuth consent steps above. Ctrl+C closes
the foreground tunnel. No background service or startup task is installed.
`tunnel status` displays the recorded URL and PID; after an abrupt process kill this
record can be stale. If ngrok assigns a new origin, reset remote grants and reconnect.

Only `chatgpt.com/connector_platform_oauth_redirect` and single-segment
`chatgpt.com/connector/oauth/<callback_id>` HTTPS callbacks are accepted. The service
supports DCR, S256 PKCE, protected-resource discovery, resource-bound tokens, one-hour
access tokens, rotating 30-day refresh tokens and revocation. The upstream WHOOP token
stays in the encrypted local store. No ChatGPT API key is needed for this server.

Run `whoop-mcp remote reset` locally and type `RESET` to revoke all remote tokens and
registrations. Changing the public origin requires a reset and a fresh connection.
Stopping the forwarding service removes public reachability. The server itself binds
only to loopback and disables access logs.

Implementation references, checked 2026-10-22:
[OpenAI plugin authentication](https://developers.openai.com/plugins/build/auth),
[MCP server guidance](https://developers.openai.com/api/docs/mcp).
