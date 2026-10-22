# Run this in your own PowerShell window. Never paste secrets into chat.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create the project virtual environment first; see docs/installation.md.' }
Write-Host 'WHOOP MCP by Das Kreb - local account setup'
Write-Host 'Register http://127.0.0.1:8937/callback in your WHOOP developer application.'
Write-Host 'The client secret is hidden and saved only in encrypted local storage.'
Start-Process 'https://developer.whoop.com/' -WindowStyle Hidden
& $python -m whoop_mcp.cli setup
if ($LASTEXITCODE -ne 0) { throw 'Setup did not finish.' }
& $python -m whoop_mcp.cli login
if ($LASTEXITCODE -ne 0) { throw 'Login did not finish.' }
& $python -m whoop_mcp.cli verify
if ($LASTEXITCODE -ne 0) { throw 'Authenticated verification failed.' }
Write-Host 'Account connection verified. Tell Codex that setup succeeded; do not send credentials.'
