# WHOOP MCP

<img src="assets/branding/das-kreb-logo.png" width="240" alt="Das Kreb">

By **Das Kreb**. Private recovery, sleep and training conversations, powered by the official WHOOP API.

[![Tests](https://github.com/myke239/whoop-mcp/actions/workflows/tests.yml/badge.svg)](https://github.com/myke239/whoop-mcp/actions/workflows/tests.yml)
[![MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**[Project website](https://myke239.github.io/whoop-mcp/)** · **[Download](https://github.com/myke239/whoop-mcp/releases)** · **[Install](docs/installation.md)** · **[Documentation](docs/README.md)**

Bring WHOOP data into Codex or another MCP assistant. Explore your recovery, sleep and
recorded training, then compare periods with explicit units and missing values.
An optional personal HTTPS endpoint supports OAuth connections from ChatGPT where
your account allows them. Phone availability requires account-level verification.

## What you can do

| Ask | What the server provides |
| --- | --- |
| “How has my recovery changed over two weeks?” | Recovery %, HRV ms, resting HR bpm and bounded comparisons |
| “Review my primary sleep and naps.” | Sleep records, stage milliseconds, performance and consistency |
| “Compare my recorded workouts.” | Strain, heart rate, HR zones, energy kJ and distance m when present |
| “What evidence is available for today?” | Local-date view with recovery and sleep joined by exact cycle IDs |
| “What are the data limits?” | Queryable guide, fixed page caps and explicit pagination completeness |

## Get started

Install from source with Python 3.12+ using `scripts/install.ps1 -Plugin` on Windows
or `sh scripts/install.sh --plugin` on macOS/Linux. The installer prints the absolute
launcher path. Native release archives, when available, include a Python runtime.

Run the installed launcher with `setup`, `login`, and `verify`. Configuration prompts
and browser consent stay on your machine. Enable the **WHOOP** plugin in Codex and
start a new chat. See [installation](docs/installation.md) and [Codex setup](docs/codex.md).
Never send client secrets, passwords or tokens in chat.

## Built for a private connection

- **Official API coverage.** All six public WHOOP member-data categories, physiological
  cycle joins, daily evidence, summaries and comparisons across 15 focused tools.
- **Guided use.** Three plugin skills cover training, recovery and daily check-ins;
  every MCP client can query the same capabilities and units from the server.
- **Encrypted local authorization.** WHOOP OAuth tokens use OS-keyring-backed encryption,
  atomic state updates and serialized refresh rotation. Unsupported keyrings fail closed.
- **Separate remote consent.** Personal HTTP uses OAuth, S256 PKCE, local terminal
  approval, resource-bound tokens, rotation and revocation. No public unauthenticated data.
- **Inspectable distribution.** Cross-platform managed installers, native target-OS
  builds, CI, checksums, privacy documentation and a public MIT-licensed repository.

## Compatibility and limits

The current implementation uses Python 3.12+ and the official WHOOP API v2.
WHOOP's public member API is read-only for training data: workout creation/scheduling,
journal edits, alarms, steps, continuous HR samples and FIT archives are not available.
Trusted-partner laboratory APIs are outside this connector's scope.

This is self-hosted software for one owner. Linux requires an unlocked Secret Service;
macOS uses Keychain and Windows uses Credential Manager. Remote access requires a
trusted HTTPS forwarding service and an awake server machine.
Executables are unsigned unless a release explicitly states otherwise.

Local offline tests cover real stdio MCP, HTTP OAuth and synthetic API responses.
Live WHOOP authorization, ChatGPT acceptance and phone use have not yet been verified.
See [verification evidence](docs/verification.md) for the distinction between implementation,
automated checks and account-level acceptance. Metrics support descriptive conversations,
not medical diagnosis or clearance.

## Support and contribution

Read [troubleshooting](docs/troubleshooting.md), then [open an issue](https://github.com/myke239/whoop-mcp/issues)
with a redacted reproduction. Do not upload credentials or health records. Report
vulnerabilities privately using [SECURITY.md](SECURITY.md).
Contributions follow branch → PR → checks → merge; see [CONTRIBUTING.md](CONTRIBUTING.md).
Dependencies retain their own licenses; see [NOTICE](NOTICE).

Independent project; not affiliated with WHOOP or OpenAI.
