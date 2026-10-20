param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('install','start','stop','update','check','enable-logon')]
    [string]$Action,
    [string]$State = 'D:\BursarBridge-live-state',
    [string]$Checkout = 'D:\BursarBridge-live',
    [string]$Hostname = 'bursarbridge.noamofficial.vn',
    [string]$EnvFile,
    [string]$WslDistro
)
$ErrorActionPreference = 'Stop'
$frozenRunner = Join-Path $State 'tools\live.py'
$livePython = Join-Path $Checkout 'services\api\.venv\Scripts\python.exe'
if ($Action -ne 'install' -and (Test-Path -LiteralPath $frozenRunner) -and (Test-Path -LiteralPath $livePython)) {
    $runner = $frozenRunner
    $python = $livePython
} else {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
    & uv sync --project (Join-Path $repoRoot 'services\api') --frozen
    if ($LASTEXITCODE -ne 0) { throw 'Python setup failed' }
    $python = Join-Path $repoRoot 'services\api\.venv\Scripts\python.exe'
    $runner = Join-Path $PSScriptRoot 'live.py'
}
$runnerArgs = @($runner, $Action, '--state', $State, '--checkout', $Checkout, '--hostname', $Hostname)
if ($EnvFile) { $runnerArgs += @('--env-file', (Resolve-Path -LiteralPath $EnvFile).Path) }
if ($WslDistro) { $runnerArgs += @('--wsl-distro', $WslDistro) }
& $python @runnerArgs
if ($LASTEXITCODE -ne 0) { throw 'Live stack command failed; see the private state/logs directory' }
