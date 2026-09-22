param(
    [Parameter(Mandatory = $true)]
    [string]$Config
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------
# Resolve repository paths
# ---------------------------------------------------------
$RepoRoot      = Split-Path -Parent $PSScriptRoot
$ConfigPath    = Join-Path $RepoRoot "simulator\configs\$Config"
$PreflightPath = Join-Path $PSScriptRoot "azure_eventhubs_preflight.bat"

if (-not (Test-Path $ConfigPath)) {
    throw "Config file not found: $ConfigPath"
}

# ---------------------------------------------------------
# Read execution metadata directly from YAML
# ---------------------------------------------------------
$PythonCode = @'
import json
import sys
import yaml

path = sys.argv[1]

with open(path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

eh = cfg.get('publishers', {}).get('event_hubs', {})

print(json.dumps({
    'run_id': cfg['simulation_context']['simulator_run_id'],
    'event_hubs_enabled': bool(eh.get('enabled', False)),
    'event_hubs_namespace': eh.get('fully_qualified_namespace', ''),
}))
'@

$MetadataJson = & python -c $PythonCode $ConfigPath

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($MetadataJson)) {
    throw "Could not read execution metadata from $Config"
}

$Metadata = $MetadataJson | ConvertFrom-Json
$RunId = [string]$Metadata.run_id

if ([string]::IsNullOrWhiteSpace($RunId)) {
    throw "simulation_context.simulator_run_id is empty in $Config"
}

$RunId = $RunId.Trim()

# ---------------------------------------------------------
# Cloud pre-flight
#
# Runs only when Event Hubs publishing is enabled. This is
# intentionally before output directory creation, so an auth
# or network failure does not consume a RunId locally.
# ---------------------------------------------------------
if ([bool]$Metadata.event_hubs_enabled) {

    if (-not (Test-Path $PreflightPath)) {
        throw "Azure preflight script not found: $PreflightPath"
    }

    $Namespace = [string]$Metadata.event_hubs_namespace

    if ([string]::IsNullOrWhiteSpace($Namespace)) {
        throw "Event Hubs is enabled but fully_qualified_namespace is empty in $Config"
    }

    Write-Host ""
    Write-Host "[AZURE PREFLIGHT] Event Hubs publishing is enabled."

    & $PreflightPath $Namespace
    $PreflightExitCode = $LASTEXITCODE

    if ($PreflightExitCode -ne 0) {
        throw "Azure/Event Hubs preflight failed with exit code $PreflightExitCode"
    }
}

# ---------------------------------------------------------
# Prepare run artifact directory
# ---------------------------------------------------------
$RunDir     = Join-Path $RepoRoot "output\$RunId"
$ConsoleLog = Join-Path $RunDir "console_output.txt"

# Guard against accidental RunId reuse on this machine
if (Test-Path $RunDir) {
    throw @"
Run directory already exists:

$RunDir

RunId '$RunId' may already have been used.
Use a new simulator_run_id before running again.
"@
}

New-Item -ItemType Directory -Path $RunDir | Out-Null

# ---------------------------------------------------------
# Show execution plan
# ---------------------------------------------------------
Write-Host ""
Write-Host "============================================================"
Write-Host " SIMULATION RUNNER"
Write-Host "============================================================"
Write-Host "Config : $Config"
Write-Host "RunId  : $RunId"
Write-Host "Output : $RunDir"
Write-Host "Python : $((Get-Command python).Source)"
Write-Host "============================================================"
Write-Host ""

# ------------------------------------------------------------
# Execute simulator and preserve full native stdout/stderr
# ------------------------------------------------------------
$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$PythonExitCode = 1

try {
    python -m simulator.fleet_main `
        --config $ConfigPath 2>&1 |
        Tee-Object -FilePath $ConsoleLog

    $PythonExitCode = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $PreviousErrorActionPreference
}

if ($PythonExitCode -ne 0) {
    Write-Host ""
    Write-Host "============================================================"
    Write-Host " SIMULATION FAILED"
    Write-Host "============================================================"
    Write-Host "Exit code : $PythonExitCode"
    Write-Host "Console   : $ConsoleLog"
    Write-Host "============================================================"

    throw "Simulation failed with exit code $PythonExitCode. See $ConsoleLog"
}

# ---------------------------------------------------------
# Final status
# ---------------------------------------------------------
Write-Host ""
Write-Host "============================================================"
Write-Host " RUN COMPLETED"
Write-Host "============================================================"
Write-Host "RunId         : $RunId"
Write-Host "Exit code     : $PythonExitCode"
Write-Host "Console output: $ConsoleLog"
Write-Host "Artifacts     : $RunDir"
Write-Host "============================================================"
