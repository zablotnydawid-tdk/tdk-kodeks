param(
    [string]$Root = "C:\KODEKS",
    [string]$HistoryRoot = ""
)

$ErrorActionPreference = "Continue"

if (-not $HistoryRoot) {
    $HistoryRoot = Join-Path $Root "state\history"
}

function Read-JsonFile {
    param([string]$Path)

    try {
        return Get-Content -Raw -Path $Path | ConvertFrom-Json
    }
    catch {
        Write-Host "invalid snapshot skipped: $Path" -ForegroundColor Yellow
        return $null
    }
}

function Get-StatusRank {
    param([string]$Status)
    switch ($Status) {
        "active" { return 0 }
        "unknown" { return 1 }
        "warning" { return 2 }
        "error" { return 3 }
        default { return 1 }
    }
}

function Get-DriftRank {
    param([string]$DriftLevel)
    switch ($DriftLevel) {
        "none" { return 0 }
        "low" { return 1 }
        "medium" { return 2 }
        "high" { return 3 }
        default { return 0 }
    }
}

function Get-OverallState {
    param(
        [object[]]$Components,
        [object]$RetinaDashboard
    )

    $statuses = @($Components | ForEach-Object { $_.status })
    if ($statuses -contains "error") {
        return "error"
    }
    if ($statuses -contains "warning") {
        return "warning"
    }
    if ($statuses -contains "unknown") {
        $unknownComponents = @($Components | Where-Object { $_.status -eq "unknown" })
        if (
            $unknownComponents.Count -eq 1 -and
            $null -ne $RetinaDashboard -and
            $unknownComponents[0] -eq $RetinaDashboard -and
            $RetinaDashboard.notes -like "*blueprinted as read-only preview*"
        ) {
            return "active-with-planned-components"
        }
        return "unknown"
    }
    return "active"
}

function Get-MaxDriftLevel {
    param([object[]]$Components)

    $maxRank = -1
    $maxDrift = "none"
    foreach ($component in $Components) {
        $rank = Get-DriftRank $component.drift_level
        if ($rank -gt $maxRank) {
            $maxRank = $rank
            $maxDrift = $component.drift_level
        }
    }
    return $maxDrift
}

function Get-StatusColor {
    param([string]$Status)
    switch ($Status) {
        "active" { return "Green" }
        "active-with-planned-components" { return "Green" }
        "warning-free-planned" { return "Green" }
        "warning" { return "Yellow" }
        "error" { return "Red" }
        "unknown" { return "DarkGray" }
        default { return "Gray" }
    }
}

function Get-ComponentValues {
    param([object]$Snapshot)

    if ($null -eq $Snapshot.components) {
        return @()
    }
    return @($Snapshot.components.PSObject.Properties | ForEach-Object { $_.Value })
}

if (-not (Test-Path $HistoryRoot)) {
    Write-Host "history folder missing: $HistoryRoot" -ForegroundColor Yellow
    exit 1
}

$files = @(
    Get-ChildItem $HistoryRoot -Filter "control_plane_status_*.json" -File |
        Sort-Object Name -Descending
)

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "    TDK CONTROL PLANE :: RETINA TIMELINE LITE" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ("history: {0}" -f $HistoryRoot)
Write-Host ""

if ($files.Count -eq 0) {
    Write-Host "no history snapshots found" -ForegroundColor Yellow
    exit 1
}

Write-Host ("{0,-22} {1,-44} {2,-32} {3,-8} {4,-6} {5}" -f "timestamp", "filename", "overall", "warnings", "errors", "max_drift")
Write-Host ("{0,-22} {1,-44} {2,-32} {3,-8} {4,-6} {5}" -f "---------", "--------", "-------", "--------", "------", "---------")

$shown = 0
foreach ($file in $files) {
    $snapshot = Read-JsonFile -Path $file.FullName
    if ($null -eq $snapshot) {
        continue
    }

    $components = Get-ComponentValues -Snapshot $snapshot
    $warnings = @($components | Where-Object { $_.status -eq "warning" }).Count
    $errors = @($components | Where-Object { $_.status -eq "error" }).Count
    $overall = Get-OverallState -Components $components -RetinaDashboard $snapshot.components.retina_dashboard
    $maxDrift = Get-MaxDriftLevel -Components $components
    $color = Get-StatusColor $overall
    $line = "{0,-22} {1,-44} {2,-32} {3,-8} {4,-6} {5}" -f `
        $snapshot.generated_at,
        $file.Name,
        $overall,
        $warnings,
        $errors,
        $maxDrift
    Write-Host $line -ForegroundColor $color
    $shown += 1
}

Write-Host ""
Write-Host ("snapshots shown: {0}" -f $shown)
Write-Host ""
exit 0
