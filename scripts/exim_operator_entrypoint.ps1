param(
    [string]$Root = "C:\KODEKS",
    [ValidateSet("none", "live_case_demo", "timeline", "operator_actions", "continuity_benchmark")]
    [string]$Launch = "none",
    [switch]$Interactive
)

$ErrorActionPreference = "Continue"

$ControlPlanePath = Join-Path $Root "state\control_plane_status.json"
$HistoryRoot = Join-Path $Root "state\history"
$FinalAxisLogPath = Join-Path $Root "data\final_axis\runtime_log.jsonl"
$ContinuityStatePath = Join-Path $Root "data\vma\vma_continuity_state.json"
$LiveCasePath = Join-Path $Root "data\live_ops\live_case_result.json"
$DriftLogPath = Join-Path $Root "data\drift_energy_monitor\runtime_log.jsonl"
$DriftReportPath = Join-Path $Root "data\drift_energy_monitor\operational_report.md"
$KnowledgeLayerPath = Join-Path $Root "knowledge\document_ingestor.py"
$KnowledgeRunbookPath = Join-Path $Root "docs\runbooks\exim_knowledge_ingestion_engine.md"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host ("== {0} ==" -f $Title) -ForegroundColor Cyan
}

function Write-Kv {
    param(
        [string]$Key,
        [object]$Value,
        [string]$Color = "Gray"
    )
    if ($null -eq $Value -or [string]::IsNullOrWhiteSpace([string]$Value)) {
        $Value = "UNKNOWN"
        $Color = "Yellow"
    }
    Write-Host ("{0,-28} {1}" -f ($Key + ":"), $Value) -ForegroundColor $Color
}

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        return $null
    }
    try {
        return Get-Content -Raw -Path $Path | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

function Read-LatestJsonLine {
    param(
        [string]$Path,
        [string]$RecordType = ""
    )
    if (-not (Test-Path $Path)) {
        return $null
    }
    $lines = @(Get-Content -Path $Path | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    [array]::Reverse($lines)
    foreach ($line in $lines) {
        try {
            $item = $line | ConvertFrom-Json
            if (-not $RecordType -or $item.record_type -eq $RecordType) {
                return $item
            }
        }
        catch {
            continue
        }
    }
    return $null
}

function Get-LatestControlPlaneHistory {
    if (-not (Test-Path $HistoryRoot)) {
        return $null
    }
    $file = Get-ChildItem $HistoryRoot -Filter "control_plane_status_*.json" -File |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 1
    if (-not $file) {
        return $null
    }
    return [pscustomobject]@{
        Path = $file.FullName
        Snapshot = Read-JsonFile -Path $file.FullName
    }
}

function Get-ObjectPropertyValues {
    param([object]$Object)
    if ($null -eq $Object) {
        return @()
    }
    return @($Object.PSObject.Properties | ForEach-Object { $_.Value })
}

function Get-ComponentSummary {
    param([object]$ControlPlane)
    $components = Get-ObjectPropertyValues -Object $ControlPlane.components
    $warnings = @($components | Where-Object { $_.status -eq "warning" }).Count
    $unknown = @($components | Where-Object { $_.status -eq "unknown" }).Count
    $errors = @($components | Where-Object { $_.status -eq "error" }).Count
    $active = @($components | Where-Object { $_.status -eq "active" }).Count
    $maxDrift = "UNKNOWN"
    $driftRank = @{ "none" = 0; "low" = 1; "medium" = 2; "high" = 3 }
    $bestRank = -1
    foreach ($component in $components) {
        $level = [string]$component.drift_level
        if ($driftRank.ContainsKey($level) -and $driftRank[$level] -gt $bestRank) {
            $bestRank = $driftRank[$level]
            $maxDrift = $level
        }
    }
    return [pscustomobject]@{
        Total = $components.Count
        Active = $active
        Warnings = $warnings
        Unknown = $unknown
        Errors = $errors
        MaxDrift = $maxDrift
    }
}

function Get-PathStatus {
    param([string]$Path)
    if (Test-Path $Path) {
        return "present"
    }
    return "missing"
}

function Add-MissingHint {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Hint
    )
    if (-not (Test-Path $Path)) {
        return [pscustomobject]@{
            Name = $Name
            Path = $Path
            Hint = $Hint
        }
    }
    return $null
}

function Get-RecommendedAction {
    param(
        [array]$Missing,
        [object]$Continuity,
        [object]$Drift,
        [object]$LiveCase,
        [object]$ControlSummary
    )
    if ($Missing.Count -gt 0) {
        return "SAFE MODE: recover missing runtime data before launching optional flows."
    }
    if ($ControlSummary.Errors -gt 0) {
        return "Review Control Plane errors, keep runtime observe-only, then run operator actions preview."
    }
    if ($null -ne $Drift -and $Drift.state_after -eq "critical") {
        return "Hold autonomous actions; review DEMON critical findings and recovery plan."
    }
    if ($null -ne $LiveCase -and $LiveCase.priority.level -eq "critical") {
        return "Review latest live case intake, evidence gaps, and operator-gated next actions."
    }
    if ($null -ne $Continuity -and $Continuity.recovery_required -eq $true) {
        return "Restore continuity anchor before expanding scope or launching demos."
    }
    if ($ControlSummary.Warnings -gt 0 -or $ControlSummary.Unknown -gt 0) {
        return "Run Control Plane verification and inspect planned/unknown components."
    }
    return "Continue observe-only operations; launch timeline or continuity benchmark only if operator needs proof."
}

function Write-ContinuityComment {
    param([object]$Continuity)
    if ($null -eq $Continuity) {
        Write-Kv "continuity comment" "UNKNOWN - state file missing; do not infer operator memory."
        return
    }
    if ($Continuity.recovery_required -eq $true) {
        Write-Kv "continuity comment" "Recovery required; restore anchor before expanding." "Yellow"
        return
    }
    if ($Continuity.continuity_score -ge 0.9) {
        Write-Kv "continuity comment" "Anchor preserved; expansion can remain operator-gated." "Green"
        return
    }
    Write-Kv "continuity comment" "Continuity bounded but not maximal; keep comments short and anchored." "Yellow"
}

function Invoke-OptionalLaunch {
    param([string]$Target)
    if ($Target -eq "none") {
        return
    }
    Write-Section "Optional Launch"
    switch ($Target) {
        "live_case_demo" {
            Write-Host "launching scripts\live_case_demo.ps1"
            & (Join-Path $Root "scripts\live_case_demo.ps1") -Root $Root
        }
        "timeline" {
            Write-Host "launching scripts\show_control_plane_timeline.ps1"
            & (Join-Path $Root "scripts\show_control_plane_timeline.ps1") -Root $Root
        }
        "operator_actions" {
            Write-Host "launching scripts\control_plane_actions.ps1 -Preview"
            & (Join-Path $Root "scripts\control_plane_actions.ps1") -Root $Root -Preview
        }
        "continuity_benchmark" {
            Write-Host "launching scripts\vma_continuity_benchmark.ps1"
            & (Join-Path $Root "scripts\vma_continuity_benchmark.ps1") -Root $Root
        }
    }
}

if (-not (Test-Path $Root)) {
    Write-Host "EXIM OPERATOR ENTRYPOINT" -ForegroundColor Cyan
    Write-Host ("Root missing: {0}" -f $Root) -ForegroundColor Red
    Write-Host "SAFE MODE: UNKNOWN. Recovery hint: run from C:\KODEKS or pass -Root."
    exit 2
}

$controlPlane = Read-JsonFile -Path $ControlPlanePath
$latestHistory = Get-LatestControlPlaneHistory
$runtimeState = Read-LatestJsonLine -Path $FinalAxisLogPath
$continuityState = Read-JsonFile -Path $ContinuityStatePath
$liveCase = Read-JsonFile -Path $LiveCasePath
$driftState = Read-LatestJsonLine -Path $DriftLogPath -RecordType "analysis"
$controlSummary = Get-ComponentSummary -ControlPlane $controlPlane

$missing = @()
$missing += Add-MissingHint "Control Plane snapshot" $ControlPlanePath "run scripts\generate_control_plane_snapshot.ps1"
$missing += Add-MissingHint "Final Axis runtime log" $FinalAxisLogPath "run python scripts\run_final_axis.py"
$missing += Add-MissingHint "VMA continuity state" $ContinuityStatePath "run scripts\vma_continuity_benchmark.ps1"
$missing += Add-MissingHint "Live Case result" $LiveCasePath "run scripts\live_case_demo.ps1"
$missing += Add-MissingHint "DEMON runtime log" $DriftLogPath "run python scripts\run_drift_energy_monitor.py"
$missing = @($missing | Where-Object { $null -ne $_ })

$safeMode = "OBSERVE_ONLY"
if ($missing.Count -gt 0) {
    $safeMode = "SAFE_MODE_DEGRADED_READ_ONLY"
}

$recommendedAction = Get-RecommendedAction `
    -Missing $missing `
    -Continuity $continuityState `
    -Drift $driftState `
    -LiveCase $liveCase `
    -ControlSummary $controlSummary

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "        EXIM OPERATOR ENTRYPOINT" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Kv "root" $Root
Write-Kv "runtime mode" "local-first / terminal-first / read-only by default" "Green"
Write-Kv "cloud runtime" "disabled" "Green"
Write-Kv "safe mode" $safeMode $(if ($safeMode -eq "OBSERVE_ONLY") { "Green" } else { "Yellow" })

Write-Section "Organism State"
Write-Kv "control plane snapshot" (Get-PathStatus $ControlPlanePath) $(if (Test-Path $ControlPlanePath) { "Green" } else { "Yellow" })
Write-Kv "generated_at" $controlPlane.generated_at
Write-Kv "workspace" $controlPlane.operator_context.workspace
Write-Kv "components total" $controlSummary.Total
Write-Kv "components active" $controlSummary.Active "Green"
Write-Kv "warnings" $controlSummary.Warnings $(if ($controlSummary.Warnings -gt 0) { "Yellow" } else { "Green" })
Write-Kv "unknown" $controlSummary.Unknown $(if ($controlSummary.Unknown -gt 0) { "Yellow" } else { "Green" })
Write-Kv "errors" $controlSummary.Errors $(if ($controlSummary.Errors -gt 0) { "Red" } else { "Green" })
Write-Kv "max component drift" $controlSummary.MaxDrift
if ($latestHistory) {
    Write-Kv "latest history snapshot" ([System.IO.Path]::GetFileName($latestHistory.Path))
}
else {
    Write-Kv "latest history snapshot" "UNKNOWN"
}

Write-Section "Last Runtime State"
Write-Kv "runtime log" (Get-PathStatus $FinalAxisLogPath) $(if (Test-Path $FinalAxisLogPath) { "Green" } else { "Yellow" })
Write-Kv "record_type" $runtimeState.record_type
Write-Kv "logged_at" $runtimeState.logged_at
if ($runtimeState.after) {
    Write-Kv "mode" $runtimeState.after.mode
    Write-Kv "boundary" $runtimeState.after.active_boundary
    Write-Kv "confined" $runtimeState.after.confined
    Write-Kv "drift_score" $runtimeState.after.drift_score
}
elseif ($runtimeState.action) {
    Write-Kv "action" $runtimeState.action
    Write-Kv "status" $runtimeState.status
    Write-Kv "trace_id" $runtimeState.trace_id
}
else {
    Write-Kv "mode" "UNKNOWN"
}

Write-Section "Continuity State"
Write-Kv "continuity file" (Get-PathStatus $ContinuityStatePath) $(if (Test-Path $ContinuityStatePath) { "Green" } else { "Yellow" })
Write-Kv "active" $continuityState.active
Write-Kv "topic" $continuityState.current_topic
Write-Kv "layer" $continuityState.current_layer
Write-Kv "continuity_score" $continuityState.continuity_score
Write-Kv "topology_retention" $continuityState.topology_retention_score
Write-Kv "recovery_required" $continuityState.recovery_required
Write-Kv "recursive_stability" $continuityState.recursive_stability
Write-ContinuityComment -Continuity $continuityState

Write-Section "Drift / Risk State"
Write-Kv "demon log" (Get-PathStatus $DriftLogPath) $(if (Test-Path $DriftLogPath) { "Green" } else { "Yellow" })
Write-Kv "report" (Get-PathStatus $DriftReportPath) $(if (Test-Path $DriftReportPath) { "Green" } else { "Yellow" })
Write-Kv "snapshot_id" $driftState.snapshot_id
Write-Kv "state_before" $driftState.state_before
Write-Kv "state_after" $driftState.state_after $(if ($driftState.state_after -eq "critical") { "Red" } elseif ($driftState.state_after) { "Green" } else { "Yellow" })
Write-Kv "findings" @($driftState.findings).Count
if ($driftState.metrics) {
    Write-Kv "coherence_index" $driftState.metrics.coherence_index
    Write-Kv "runtime_entropy" $driftState.metrics.runtime_entropy
    Write-Kv "economic_drift" $driftState.metrics.economic_drift
}

Write-Section "Active Live Case"
Write-Kv "live case file" (Get-PathStatus $LiveCasePath) $(if (Test-Path $LiveCasePath) { "Green" } else { "Yellow" })
Write-Kv "case_id" $liveCase.case_id
Write-Kv "title" $liveCase.intake.title
Write-Kv "priority" $liveCase.priority.level $(if ($liveCase.priority.level -eq "critical") { "Red" } elseif ($liveCase.priority.level) { "Green" } else { "Yellow" })
Write-Kv "operator decision" $liveCase.classification.operator_decision_required
Write-Kv "autonomous action" $liveCase.priority.autonomous_action_allowed
if ($liveCase.recommendation.operator_next_actions) {
    Write-Kv "next operator action" $liveCase.recommendation.operator_next_actions[0]
}
else {
    Write-Kv "next operator action" "UNKNOWN"
}

Write-Section "Complex Knowledge Layer"
Write-Kv "knowledge ingestion" (Get-PathStatus $KnowledgeLayerPath) $(if (Test-Path $KnowledgeLayerPath) { "Green" } else { "Yellow" })
Write-Kv "runbook" (Get-PathStatus $KnowledgeRunbookPath) $(if (Test-Path $KnowledgeRunbookPath) { "Green" } else { "Yellow" })
Write-Kv "default posture" "trace-first / human-review-gated / no cloud OCR" "Green"
Write-Kv "recommendation gate" "source trace + domain classification + human validation"

Write-Section "Recovery Hints"
if ($missing.Count -eq 0) {
    Write-Kv "missing runtime data" "none" "Green"
}
else {
    foreach ($item in $missing) {
        Write-Host ("{0}: UNKNOWN" -f $item.Name) -ForegroundColor Yellow
        Write-Host ("  path: {0}" -f $item.Path)
        Write-Host ("  recovery: {0}" -f $item.Hint)
    }
}

Write-Section "Recommended Operator Action"
Write-Host $recommendedAction -ForegroundColor $(if ($safeMode -eq "OBSERVE_ONLY") { "Green" } else { "Yellow" })

Write-Section "Optional Local Launch"
Write-Host ".\scripts\exim_operator_entrypoint.ps1 -Launch timeline"
Write-Host ".\scripts\exim_operator_entrypoint.ps1 -Launch operator_actions"
Write-Host ".\scripts\exim_operator_entrypoint.ps1 -Launch live_case_demo"
Write-Host ".\scripts\exim_operator_entrypoint.ps1 -Launch continuity_benchmark"

if ($Interactive -and $Launch -eq "none") {
    Write-Host ""
    $choice = Read-Host "Optional launch (none/timeline/operator_actions/live_case_demo/continuity_benchmark)"
    if ($choice -in @("timeline", "operator_actions", "live_case_demo", "continuity_benchmark")) {
        $Launch = $choice
    }
}

Invoke-OptionalLaunch -Target $Launch
