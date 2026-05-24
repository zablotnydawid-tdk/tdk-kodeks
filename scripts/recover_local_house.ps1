param(
    [Parameter(Mandatory=$true)]
    [string]$BackupPath,
    [switch]$RestoreCode,
    [switch]$RestoreRuntimeData
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupPath)) {
    throw "Backup path not found: $BackupPath"
}

Write-Host "=== TDK/KODEKS LOCAL HOUSE RECOVERY ==="
Write-Host "Backup: $BackupPath"

if (-not $RestoreCode -and -not $RestoreRuntimeData) {
    Write-Host "[DRY-RUN] No restore switches provided."
    Write-Host "Use -RestoreCode to restore KODEKS app/docs/scripts/config."
    Write-Host "Use -RestoreRuntimeData to restore orders/reports/TDK db/env."
    exit 0
}

function Restore-IfExists {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Path $Source -Destination $Destination -Recurse -Force
        Write-Host "[OK] Restored $Source -> $Destination"
    } else {
        Write-Host "[SKIP] Missing in backup: $Source"
    }
}

if ($RestoreCode) {
    Restore-IfExists "$BackupPath\KODEKS\app" "C:\KODEKS\app"
    Restore-IfExists "$BackupPath\KODEKS\docs" "C:\KODEKS\docs"
    Restore-IfExists "$BackupPath\KODEKS\scripts" "C:\KODEKS\scripts"
    Restore-IfExists "$BackupPath\KODEKS\requirements.txt" "C:\KODEKS\requirements.txt"
    Restore-IfExists "$BackupPath\KODEKS\.env.example" "C:\KODEKS\.env.example"
    Restore-IfExists "$BackupPath\KODEKS\.gitignore" "C:\KODEKS\.gitignore"
    Restore-IfExists "$BackupPath\KODEKS\render.yaml" "C:\KODEKS\render.yaml"
}

if ($RestoreRuntimeData) {
    Restore-IfExists "$BackupPath\KODEKS\data\orders" "C:\KODEKS\data\orders"
    Restore-IfExists "$BackupPath\KODEKS\data\reports" "C:\KODEKS\data\reports"
    Restore-IfExists "$BackupPath\TDK_backend\database\app.db" "C:\TDK\TDK_backend\database\app.db"
    Restore-IfExists "$BackupPath\TDK_front\.env" "C:\TDK\TDK_front\.env"
}

Write-Host "[DONE] Recovery completed. Run start_local_house.ps1 and monitor after restore."
