param(
    [string]$Root = "C:\KODEKS",
    [string]$SnapshotPath = "",
    [string]$SchemaPath = ""
)

$ErrorActionPreference = "Continue"

if (-not $SnapshotPath) {
    $SnapshotPath = Join-Path $Root "state\control_plane_status.json"
}
if (-not $SchemaPath) {
    $SchemaPath = Join-Path $Root "schemas\control_plane_status.schema.json"
}

$GenerateScript = Join-Path $Root "scripts\generate_control_plane_snapshot.ps1"
$ValidateScript = Join-Path $Root "scripts\validate_control_plane_snapshot.ps1"
$ShowScript = Join-Path $Root "scripts\show_control_plane.ps1"
$HistoryRoot = Join-Path $Root "state\history"

function Stop-MissingDependency {
    param([string]$Path)
    Write-Host "missing dependency: $Path" -ForegroundColor Red
    exit 2
}

foreach ($requiredPath in @($GenerateScript, $ValidateScript, $ShowScript, $SchemaPath)) {
    if (-not (Test-Path $requiredPath)) {
        Stop-MissingDependency $requiredPath
    }
}

Write-Host ""
Write-Host "TDK Control Plane operator flow" -ForegroundColor Cyan
Write-Host "1/4 generate snapshot"
$global:LASTEXITCODE = $null
& $GenerateScript -Root $Root -OutputPath $SnapshotPath
$generateExit = $LASTEXITCODE
if ($generateExit -eq 1) {
    Write-Host "snapshot generation failed with controlled error" -ForegroundColor Red
    exit 2
}
elseif ($generateExit -eq 2) {
    Write-Host "snapshot generation failed because a dependency is missing" -ForegroundColor Red
    exit 2
}
elseif ($generateExit -ne 0) {
    Write-Host "snapshot generation failed with exit code $generateExit" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path $SnapshotPath)) {
    Write-Host "snapshot generation did not create: $SnapshotPath" -ForegroundColor Red
    exit 2
}

Write-Host "2/4 validate snapshot"
$global:LASTEXITCODE = $null
& $ValidateScript -Root $Root -SnapshotPath $SnapshotPath -SchemaPath $SchemaPath
$validateExit = $LASTEXITCODE
if ($validateExit -ne 0) {
    Write-Host "validation failed; Retina Lite will not start" -ForegroundColor Red
    exit 1
}

Write-Host "3/4 archive snapshot"
try {
    New-Item -ItemType Directory -Force -Path $HistoryRoot -ErrorAction Stop | Out-Null
    $historyStamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $historyPath = Join-Path $HistoryRoot "control_plane_status_$historyStamp.json"
    Copy-Item -Path $SnapshotPath -Destination $historyPath -Force -ErrorAction Stop
    Write-Host "snapshot archived: $historyPath"
}
catch {
    Write-Host "snapshot archive failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

Write-Host "4/4 show Retina Lite"
$global:LASTEXITCODE = $null
& $ShowScript -Root $Root -SnapshotPath $SnapshotPath
$showExit = $LASTEXITCODE
if ($null -ne $showExit -and $showExit -ne 0) {
    Write-Host "Retina Lite failed with exit code $showExit" -ForegroundColor Red
    exit 2
}

exit 0
