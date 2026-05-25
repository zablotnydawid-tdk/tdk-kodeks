param(
    [string]$Root = "C:\KODEKS",
    [string]$SnapshotPath = ""
)

$ErrorActionPreference = "Continue"

if (-not $SnapshotPath) {
    $SnapshotPath = Join-Path $Root "state\control_plane_status.json"
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

function Write-Header {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "          TDK CONTROL PLANE :: RETINA LITE" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
}

function Write-Section {
    param(
        [string]$Title,
        [object[]]$Rows
    )

    Write-Host ""
    Write-Host "[$Title]" -ForegroundColor Cyan
    Write-Host ("{0,-28} {1,-10} {2,-10} {3,-22} {4}" -f "component", "status", "drift", "last_checked", "next_action")
    Write-Host ("{0,-28} {1,-10} {2,-10} {3,-22} {4}" -f "---------", "------", "-----", "------------", "-----------")

    foreach ($row in $Rows) {
        $component = $row.Component
        $color = Get-StatusColor $component.status
        $line = "{0,-28} {1,-10} {2,-10} {3,-22} {4}" -f `
            $row.Key,
            $component.status,
            $component.drift_level,
            $component.last_checked,
            $component.next_action
        Write-Host $line -ForegroundColor $color
    }
}

function Write-OperatorActionsSection {
    param(
        [string]$Root,
        [string]$SnapshotPath
    )

    $actions = @(
        "repo_sync_check",
        "workspace_clean_check",
        "python_env_check",
        "node_env_check",
        "history_cleanup_preview",
        "history_cleanup_confirmed",
        "control_plane_verify"
    )

    $validateScript = Join-Path $Root "scripts\validate_control_plane_snapshot.ps1"
    $verificationStatus = "validator missing"
    $verificationColor = "Yellow"

    if (Test-Path $validateScript) {
        $validationLines = & $validateScript -Root $Root -SnapshotPath $SnapshotPath 6>&1 2>&1
        $validationOutput = ($validationLines | Out-String).Trim()
        if ($LASTEXITCODE -eq 0) {
            $verificationStatus = $validationOutput
            $verificationColor = "Green"
        }
        else {
            $verificationStatus = "validation-failed: $validationOutput"
            $verificationColor = "Red"
        }
    }

    Write-Host ""
    Write-Host "[7. OPERATOR ACTIONS]" -ForegroundColor Cyan
    Write-Host ("available actions: {0}" -f ($actions -join ", "))
    Write-Host ("last verification status: {0}" -f $verificationStatus) -ForegroundColor $verificationColor
    Write-Host "run: .\scripts\control_plane_actions.ps1 -Action <action>"
}

function Get-ComponentRow {
    param(
        [object]$Components,
        [string]$Key
    )

    return [pscustomobject]@{
        Key = $Key
        Component = $Components.$Key
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

if (-not (Test-Path $SnapshotPath)) {
    Write-Host "Snapshot missing: $SnapshotPath" -ForegroundColor Red
    Write-Host "Run: .\scripts\generate_control_plane_snapshot.ps1" -ForegroundColor Yellow
    exit 1
}

try {
    $snapshot = Get-Content -Raw -Path $SnapshotPath | ConvertFrom-Json
}
catch {
    Write-Host "Snapshot is not valid JSON: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

$components = $snapshot.components
$allComponents = @(
    $components.axis_runtime,
    $components.demon_core,
    $components.anchor_git,
    $components.github_sync,
    $components.master_system_sync,
    $components.local_operator_stack,
    $components.proservice_workflow,
    $components.retina_dashboard,
    $components.windows_environment
)

$warningCount = @($allComponents | Where-Object { $_.status -eq "warning" }).Count
$errorCount = @($allComponents | Where-Object { $_.status -eq "error" }).Count
$overall = Get-OverallState -Components $allComponents -RetinaDashboard $components.retina_dashboard
$overallColor = Get-StatusColor $overall

Write-Header
Write-Host ("snapshot: {0}" -f $SnapshotPath)
Write-Host ("generated: {0}" -f $snapshot.generated_at)
Write-Host ("workspace: {0}" -f $snapshot.operator_context.workspace)

Write-Section "1. AXIS" @(
    (Get-ComponentRow $components "axis_runtime")
)

Write-Section "2. DEMON" @(
    (Get-ComponentRow $components "demon_core")
)

Write-Section "3. GIT / ANCHOR" @(
    (Get-ComponentRow $components "github_sync"),
    (Get-ComponentRow $components "anchor_git")
)

Write-Section "4. OPERATOR STACK" @(
    (Get-ComponentRow $components "local_operator_stack"),
    (Get-ComponentRow $components "master_system_sync"),
    (Get-ComponentRow $components "proservice_workflow")
)

Write-Section "5. RETINA / UX" @(
    (Get-ComponentRow $components "retina_dashboard")
)

Write-Section "6. ENVIRONMENT" @(
    (Get-ComponentRow $components "windows_environment")
)

Write-OperatorActionsSection -Root $Root -SnapshotPath $SnapshotPath

Write-Host ""
Write-Host "----------------------------------------------"
Write-Host ("overall system state: {0}" -f $overall) -ForegroundColor $overallColor
Write-Host ("warnings: {0}" -f $warningCount) -ForegroundColor $(if ($warningCount -gt 0) { "Yellow" } else { "Green" })
Write-Host ("errors: {0}" -f $errorCount) -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host ("snapshot timestamp: {0}" -f $snapshot.generated_at)
Write-Host "----------------------------------------------"
Write-Host ""
