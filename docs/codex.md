# Codex and MCP clients

Install the server and complete local WHOOP setup, login and verify first.
Add this Git repository as a marketplace in Codex plugin settings, select **WHOOP**,
and start a new chat. The marketplace uses `whoop-mcp serve`; the launcher must be on
the Codex process PATH.

Alternatively run the installed launcher with `install-plugin`. It copies the bundled
plugin into `$CODEX_HOME/plugins/local/whoop` (default `~/.codex/plugins/local/whoop`)
and writes an absolute command into its `.mcp.json`. Add that local plugin folder in
Codex settings. Copying files alone does not establish that Codex loaded the plugin.

The three included skills guide training analysis, recovery reviews and daily check-ins.
Try “Use WHOOP to summarize my recovery over the last two weeks.” The guide tool works
without account access and is a useful initial connection check.

Other MCP clients can use this configuration, replacing the command with the full installed launcher:

```json
{"mcpServers":{"whoop":{"command":"/absolute/path/to/whoop-mcp","args":["serve"]}}}
```

All 15 tools are reads. Authentication and revocation remain interactive local commands.
