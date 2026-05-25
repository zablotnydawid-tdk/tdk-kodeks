param(
    [string]$Root = "C:\KODEKS",
    [string]$CurrentSnapshotPath = "",
    [string]$HistoryRoot = ""
)

$ErrorActionPreference = "Continue"

if (-not $CurrentSnapshotPath) {
    $CurrentSnapshotPath = Join-Path $Root "state\control_plane_status.json"
}
if (-not $HistoryRoot) {
    $HistoryRoot = Join-Path $Root "state\history"
}

function Read-JsonFile {
    param(
        [string]$Path,
        [string]$Label
    )

    if (-not (Test-Path $Path)) {
        Write-Host "$Label missing: $Path" -ForegroundColor Red
        exit 2
    }

    try {
        return Get-Content -Raw -Path $Path | ConvertFrom-Json
    }
    catch {
        Write-Host "$Label is not valid JSON: $($_.Exception.Message)" -ForegroundColor Red
        exit 2
    }
}

function Get-PreviousSnapshotPath {
    param(
        [string]$HistoryRoot,
        [string]$CurrentSnapshotGeneratedAt
    )

    if (-not (Test-Path $HistoryRoot)) {
        Write-Host "history folder missing: $HistoryRoot" -ForegroundColor Yellow
        exit 1
    }

    $historyFiles = @(
        Get-ChildItem $HistoryRoot -Filter "control_plane_status_*.json" -File |
            Sort-Object LastWriteTimeUtc -Descending
    )
    foreach ($file in $historyFiles) {
        try {
            $candidate = Get-Content -Raw -Path $file.FullName | ConvertFrom-Json
            if ($candidate.generated_at -ne $CurrentSnapshotGeneratedAt) {
                return $file.FullName
            }
        }
        catch {
            continue
        }
    }

    if ($historyFiles.Count -gt 0) {
        return $historyFiles[0].FullName
    }

    Write-Host "no history snapshots found in: $HistoryRoot" -ForegroundColor Yellow
    exit 1
}

function Get-PropertyNames {
    param([object]$Object)
    if ($null -eq $Object) {
        return @()
    }
    return @($Object.PSObject.Properties | ForEach-Object { $_.Name })
}

function Get-StatusRank {
    param([string]$Status)
    switch ($Status) {
        "active" { return 0 }
        "unknown" { return 1 }
        "warning" { return 2 }
        "error" { return 3 }
        default { return 2 }
    }
}

function Get-DriftRank {
    param([string]$DriftLevel)
    switch ($DriftLevel) {
        "none" { return 0 }
        "low" { return 1 }
        "medium" { return 2 }
        "high" { return 3 }
        default { return 2 }
    }
}

function Get-ChangeKind {
    param(
        [string]$Field,
        [string]$Before,
        [string]$After
    )

    if ($Before -eq $After) {
        return "same"
    }

    if ($Field -eq "status") {
        $beforeRank = Get-StatusRank $Before
        $afterRank = Get-StatusRank $After
        if ($afterRank -lt $beforeRank) { return "improvement" }
        if ($afterRank -gt $beforeRank) { return "regression" }
        return "neutral"
    }

    if ($Field -eq "drift_level") {
        $beforeRank = Get-DriftRank $Before
        $afterRank = Get-DriftRank $After
        if ($afterRank -lt $beforeRank) { return "improvement" }
        if ($afterRank -gt $beforeRank) { return "regression" }
        return "neutral"
    }

    return "neutral"
}

function Get-ChangeColor {
    param([string]$Kind)
    switch ($Kind) {
        "improvement" { return "Green" }
        "regression" { return "Red" }
        default { return "Yellow" }
    }
}

function Write-Change {
    param(
        [string]$Kind,
        [string]$Component,
        [string]$Field,
        [string]$Before,
        [string]$After
    )

    $color = Get-ChangeColor $Kind
    $line = "{0,-12} {1,-28} {2,-14} {3} -> {4}" -f $Kind, $Component, $Field, $Before, $After
    Write-Host $line -ForegroundColor $color
}

$current = Read-JsonFile -Path $CurrentSnapshotPath -Label "current snapshot"
$previousPath = Get-PreviousSnapshotPath -HistoryRoot $HistoryRoot -CurrentSnapshotGeneratedAt $current.generated_at
$previous = Read-JsonFile -Path $previousPath -Label "previous snapshot"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "       TDK CONTROL PLANE :: SNAPSHOT DIFF" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ("previous: {0}" -f $previousPath)
Write-Host ("previous timestamp: {0}" -f $previous.generated_at)
Write-Host ("current:  {0}" -f $CurrentSnapshotPath)
Write-Host ("current timestamp:  {0}" -f $current.generated_at)
Write-Host ""

$previousNames = Get-PropertyNames $previous.components
$currentNames = Get-PropertyNames $current.components
$allNames = @($previousNames + $currentNames | Sort-Object -Unique)
$changeCount = 0

foreach ($name in $allNames) {
    $before = $previous.components.$name
    $after = $current.components.$name

    if ($null -eq $before) {
        Write-Change "neutral" $name "component" "missing" "new"
        $changeCount += 1
        continue
    }
    if ($null -eq $after) {
        Write-Change "regression" $name "component" "present" "missing"
        $changeCount += 1
        continue
    }

    foreach ($field in @("status", "drift_level", "next_action")) {
        $beforeValue = [string]$before.$field
        $afterValue = [string]$after.$field
        $kind = Get-ChangeKind -Field $field -Before $beforeValue -After $afterValue
        if ($kind -ne "same") {
            Write-Change $kind $name $field $beforeValue $afterValue
            $changeCount += 1
        }
    }
}

if ($changeCount -eq 0) {
    Write-Host "no component changes" -ForegroundColor Green
}

Write-Host ""
Write-Host ("changes: {0}" -f $changeCount)
Write-Host ""
exit 0
