param([string]$Prefix, [switch]$Plugin, [switch]$Uninstall)
$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'install.py'
$installerArgs = @($installer)
if ($Prefix) { $installerArgs += @('--prefix', $Prefix) }
if ($Plugin) { $installerArgs += '--plugin' }
if ($Uninstall) { $installerArgs += '--uninstall' }
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $installer @($installerArgs | Select-Object -Skip 1)
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    & python3 @installerArgs
} else {
    throw 'Install Python 3.12 or newer from https://www.python.org/downloads/ and retry.'
}
if ($LASTEXITCODE -ne 0) { throw "WHOOP installer exited with code $LASTEXITCODE" }
