param(
    [Parameter(Mandatory = $true)]
    [string]$Config
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------
# Resolve repository paths
# ---------------------------------------------------------
$RepoRoot   = Split-Path -Parent $PSScriptRoot
$ConfigPath = Join-Path $RepoRoot "simulator\configs\$Config"

if (-not (Test-Path $ConfigPath)) {
    throw "Config file not found: $ConfigPath"
}

# ---------------------------------------------------------
# Read simulator_run_id directly from YAML
# ---------------------------------------------------------
$PythonCode = @'
import sys
import yaml

path = sys.argv[1]

with open(path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

print(cfg['simulation_context']['simulator_run_id'])
'@

$RunId = & python -c $PythonCode $ConfigPath

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($RunId)) {
    throw "Could not read simulation_context.simulator_run_id from $Config"
}

$RunId = $RunId.Trim()

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

# ---------------------------------------------------------
# Execute from repository root
# ---------------------------------------------------------
Push-Location $RepoRoot

try {
    python -m simulator.fleet_main `
        --config $Config 2>&1 |
        Tee-Object -FilePath $ConsoleLog

    $ExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

# ---------------------------------------------------------
# Final status
# ---------------------------------------------------------
Write-Host ""

if ($ExitCode -eq 0) {
    Write-Host "============================================================"
    Write-Host " RUN COMPLETED"
    Write-Host "============================================================"
    Write-Host "RunId         : $RunId"
    Write-Host "Console output: $ConsoleLog"
    Write-Host "Artifacts     : $RunDir"
    Write-Host "============================================================"
}
else {
    Write-Host "============================================================"
    Write-Host " RUN FAILED - ExitCode $ExitCode"
    Write-Host "============================================================"
    Write-Host "Check:"
    Write-Host $ConsoleLog
    Write-Host "============================================================"

    exit $ExitCode
}