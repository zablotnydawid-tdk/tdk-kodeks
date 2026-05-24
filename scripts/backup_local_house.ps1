$ErrorActionPreference = "Stop"

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = "C:\KODEKS\backups\local_house_$Timestamp"

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

function Copy-IfExists {
    param([string]$Source, [string]$Destination)
    if (Test-Path $Source) {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
        Copy-Item -Path $Source -Destination $Destination -Recurse -Force
        Write-Host "[OK] $Source -> $Destination"
    } else {
        Write-Host "[SKIP] Missing: $Source"
    }
}

Write-Host "=== TDK/KODEKS LOCAL HOUSE BACKUP ==="
Write-Host "Backup: $BackupRoot"

Copy-IfExists "C:\KODEKS\app" "$BackupRoot\KODEKS\app"
Copy-IfExists "C:\KODEKS\docs" "$BackupRoot\KODEKS\docs"
Copy-IfExists "C:\KODEKS\scripts" "$BackupRoot\KODEKS\scripts"
Copy-IfExists "C:\KODEKS\requirements.txt" "$BackupRoot\KODEKS\requirements.txt"
Copy-IfExists "C:\KODEKS\.env.example" "$BackupRoot\KODEKS\.env.example"
Copy-IfExists "C:\KODEKS\.gitignore" "$BackupRoot\KODEKS\.gitignore"
Copy-IfExists "C:\KODEKS\render.yaml" "$BackupRoot\KODEKS\render.yaml"
Copy-IfExists "C:\KODEKS\data\orders" "$BackupRoot\KODEKS\data\orders"
Copy-IfExists "C:\KODEKS\data\reports" "$BackupRoot\KODEKS\data\reports"
Copy-IfExists "C:\TDK\TDK_backend\database\app.db" "$BackupRoot\TDK_backend\database\app.db"
Copy-IfExists "C:\TDK\TDK_front\.env" "$BackupRoot\TDK_front\.env"
Copy-IfExists "C:\WitnessAI\WitnessAI_WhitePaper_Full.pdf" "$BackupRoot\WitnessAI\WitnessAI_WhitePaper_Full.pdf"

$Manifest = @"
# Local House Backup Manifest

Timestamp: $Timestamp
BackupRoot: $BackupRoot

Included:
- KODEKS app/docs/scripts/config
- KODEKS data/orders
- KODEKS data/reports
- TDK backend SQLite app.db
- TDK front local .env
- WitnessAI generated PDF if present

Excluded:
- .venv
- node_modules
- __pycache__
- build/dist unless separately archived
- Docker volumes
- Ollama model blobs
"@

$Manifest | Out-File -FilePath "$BackupRoot\MANIFEST.md" -Encoding utf8
Write-Host "[OK] Manifest written: $BackupRoot\MANIFEST.md"
Write-Host "BACKUP_PATH=$BackupRoot"
