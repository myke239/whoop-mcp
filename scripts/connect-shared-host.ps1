# Run in your own PowerShell. Uses existing encrypted credentials; prints no secrets.
param(
    [switch]$RestartExisting,
    [string]$GarminPython,
    [string]$GarminData = 'D:\developer\.garmin-connect-mcp',
    [string]$MfpRoot = 'D:\developer\myfitnesspal-mcp'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$whoopPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
$mfpPython = Join-Path $MfpRoot '.venv/Scripts/python.exe'
$gatewaySource = Join-Path $MfpRoot 'src/myfitnesspal_mcp/gateway.py'
foreach ($file in @($whoopPython, $mfpPython, $gatewaySource)) {
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Required file missing: $file" }
}
if (-not (Select-String -LiteralPath $gatewaySource -SimpleMatch '--whoop-port' -Quiet)) {
    throw 'Update the MyFitnessPal checkout to the merged WHOOP gateway change first.'
}
$listener = Get-NetTCPConnection -State Listen -LocalPort 8788 -ErrorAction SilentlyContinue
$existingGateway = $null
if ($listener) {
    $existingGateway = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener[0].OwningProcess)"
    if ($existingGateway.CommandLine -notmatch '-m\s+myfitnesspal_mcp\.gateway\b') {
        throw 'Port 8788 belongs to another application; nothing was stopped.'
    }
    if (-not $GarminPython -and $existingGateway.CommandLine -match '--garmin-python\s+("[^"]+"|\S+)') {
        $GarminPython = $Matches[1].Trim('"')
    }
    if (-not $RestartExisting) { throw 'Existing gateway is active. Use -RestartExisting for a brief controlled restart.' }
}
if (-not $GarminPython -or -not (Test-Path -LiteralPath $GarminPython -PathType Leaf)) {
    throw 'Provide -GarminPython with the existing installed Garmin interpreter path.'
}
if (Get-NetTCPConnection -State Listen -LocalPort 8789 -ErrorAction SilentlyContinue) {
    throw 'Port 8789 is occupied; nothing was stopped.'
}
$garminListener = Get-NetTCPConnection -State Listen -LocalPort 8787 -ErrorAction SilentlyContinue
$existingGarmin = $null
if ($garminListener) {
    $existingGarmin = Get-CimInstance Win32_Process -Filter "ProcessId=$($garminListener[0].OwningProcess)"
    if (-not $existingGateway -or $existingGarmin.CommandLine -notmatch '-m\s+garmin_connect_mcp\.remote\s+serve\b') {
        throw 'Port 8787 is not the expected gateway backend; nothing was stopped.'
    }
}
$oldPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $MfpRoot 'src'
$whoopProcess = $null
try {
    # Read only the public origin from existing DPAPI state. Never copy or print tokens.
    $origin = (& $mfpPython -c 'import sys; from myfitnesspal_mcp.gateway import read_garmin_state, public_origin; print(public_origin(read_garmin_state(sys.argv[1], "remote-oauth")["origin"]))' $GarminData).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $origin.StartsWith('https://')) { throw 'Could not read the existing public origin.' }
    $logRoot = Join-Path $projectRoot 'work/shared-host'
    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $whoopProcess = Start-Process -FilePath $whoopPython -ArgumentList @('-m','whoop_mcp.cli','remote','serve','--shared-host','--public-url',$origin,'--port','8789') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'whoop.stdout.log') -RedirectStandardError (Join-Path $logRoot 'whoop.stderr.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($whoopProcess.HasExited) { throw 'WHOOP backend exited; inspect work/shared-host/whoop.stderr.log locally.' }
        try {
            $health = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8789/mcp/whoop/health' -Headers @{Host=([uri]$origin).Host} -TimeoutSec 2
            if ($health.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw 'WHOOP backend readiness check failed.' }
    # Verify the new backend before interrupting the existing public connection.
    if ($existingGateway) {
        Write-Host 'Restarting the verified shared gateway. Existing OAuth grants are preserved.'
        & taskkill /PID $existingGateway.ProcessId /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the existing gateway.' }
    }
    if ($existingGarmin -and (Get-Process -Id $existingGarmin.ProcessId -ErrorAction SilentlyContinue)) {
        & taskkill /PID $existingGarmin.ProcessId /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Could not stop the verified Garmin backend.' }
    }
    Write-Host "WHOOP connection URL: $origin/mcp/whoop/"
    Write-Host 'Keep this terminal open. Ctrl+C stops the shared gateway and WHOOP backend.'
    & $mfpPython -m myfitnesspal_mcp.gateway --garmin-python $GarminPython --garmin-data $GarminData --whoop-port 8789
    if ($LASTEXITCODE -ne 0) { throw 'Shared gateway exited with an error.' }
} finally {
    if ($whoopProcess -and -not $whoopProcess.HasExited) {
        & taskkill /PID $whoopProcess.Id /T /F | Out-Null
    }
    $env:PYTHONPATH = $oldPythonPath
}
