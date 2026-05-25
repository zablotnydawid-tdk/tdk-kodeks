param(
    [string]$Root = "C:\KODEKS",
    [ValidateSet("all", "repo_sync_check", "workspace_clean_check", "python_env_check", "node_env_check", "history_cleanup_preview", "control_plane_verify")]
    [string]$Action = "all"
)

$ErrorActionPreference = "Continue"

function Resolve-Executable {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (-not $candidate) {
            continue
        }
        if (Test-Path $candidate) {
            $extension = [System.IO.Path]::GetExtension($candidate).ToLowerInvariant()
            if ($extension -in @(".exe", ".cmd", ".bat", ".ps1")) {
                return $candidate
            }
            continue
        }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    return ""
}

function Write-ActionResult {
    param(
        [string]$Action,
        [string]$Result,
        [string]$Recommendation,
        [string]$RiskLevel
    )

    $color = switch ($RiskLevel) {
        "none" { "Green" }
        "low" { "Green" }
        "medium" { "Yellow" }
        "high" { "Red" }
        default { "Gray" }
    }

    Write-Host ""
    Write-Host ("action:         {0}" -f $Action) -ForegroundColor Cyan
    Write-Host ("result:         {0}" -f $Result) -ForegroundColor $color
    Write-Host ("recommendation: {0}" -f $Recommendation)
    Write-Host ("risk_level:     {0}" -f $RiskLevel) -ForegroundColor $color
}

function Invoke-SnapshotValidator {
    param([string]$ValidateScript)

    $outputLines = & $ValidateScript -Root $Root 6>&1 2>&1
    return [pscustomobject]@{
        ExitCode = $LASTEXITCODE
        Output = (($outputLines | Out-String).Trim())
    }
}

function Invoke-RepoSyncCheck {
    $gitPath = Resolve-Executable @("git", "C:\Program Files\Git\cmd\git.exe", "C:\Program Files\Git\bin\git.exe")
    if (-not $gitPath) {
        Write-ActionResult "repo_sync_check" "git unavailable" "run from a shell with Git available" "medium"
        return
    }

    $head = (& $gitPath -C $Root log --oneline -1 2>$null)
    $headExitCode = $LASTEXITCODE
    if ($headExitCode -ne 0) {
        Write-ActionResult "repo_sync_check" "git log unavailable" "run git status in operator shell before push or handoff" "medium"
        return
    }

    $aheadBehind = (& $gitPath -C $Root rev-list --left-right --count origin/main...HEAD 2>$null)
    $compareExitCode = $LASTEXITCODE
    if ($compareExitCode -ne 0 -or -not $aheadBehind) {
        Write-ActionResult "repo_sync_check" "remote comparison unavailable; head=$head" "run git status in operator shell before push or handoff" "low"
        return
    }

    $parts = $aheadBehind -split "\s+"
    $behind = [int]$parts[0]
    $ahead = [int]$parts[1]
    if ($ahead -eq 0 -and $behind -eq 0) {
        Write-ActionResult "repo_sync_check" "origin/main synchronized; head=$head" "none" "none"
    }
    elseif ($ahead -gt 0 -and $behind -eq 0) {
        Write-ActionResult "repo_sync_check" "ahead by $ahead commit(s); head=$head" "push after operator review" "low"
    }
    elseif ($behind -gt 0) {
        Write-ActionResult "repo_sync_check" "behind by $behind commit(s), ahead by $ahead commit(s); head=$head" "inspect remote before further work" "medium"
    }
}

function Invoke-WorkspaceCleanCheck {
    $gitPath = Resolve-Executable @("git", "C:\Program Files\Git\cmd\git.exe", "C:\Program Files\Git\bin\git.exe")
    if (-not $gitPath) {
        Write-ActionResult "workspace_clean_check" "git unavailable" "run from a shell with Git available" "medium"
        return
    }

    $statusLines = @(& $gitPath -C $Root status --short 2>$null)
    $statusExitCode = $LASTEXITCODE
    if ($statusExitCode -ne 0) {
        Write-ActionResult "workspace_clean_check" "git status unavailable" "run git status in operator shell before handoff" "medium"
        return
    }

    if ($statusLines.Count -eq 0) {
        Write-ActionResult "workspace_clean_check" "working tree clean" "none" "none"
    }
    else {
        Write-ActionResult "workspace_clean_check" "$($statusLines.Count) pending change(s)" "review git status before handoff" "medium"
    }
}

function Invoke-PythonEnvCheck {
    $pythonPath = Resolve-Executable @((Join-Path $Root ".venv\Scripts\python.exe"), "python", "py", (Join-Path $Root ".venv\bin\python"))
    if (-not $pythonPath) {
        Write-ActionResult "python_env_check" "python unavailable" "expose Python or local .venv to operator shell" "medium"
        return
    }

    $versionLines = & $pythonPath --version 2>$null
    $version = ($versionLines | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($version)) {
        Write-ActionResult "python_env_check" "python present but version unavailable via $pythonPath" "verify Python from the operator shell before test execution" "low"
        return
    }

    Write-ActionResult "python_env_check" "$version via $pythonPath" "none" "none"
}

function Invoke-NodeEnvCheck {
    $nodePath = Resolve-Executable @("node", "C:\Program Files\nodejs\node.exe")
    if (-not $nodePath) {
        Write-ActionResult "node_env_check" "node unavailable" "install/expose Node only if dashboard build requires it" "low"
        return
    }

    $versionLines = & $nodePath --version 2>$null
    $version = ($versionLines | Select-Object -First 1)
    if ([string]::IsNullOrWhiteSpace($version)) {
        Write-ActionResult "node_env_check" "node present but version unavailable via $nodePath" "verify Node from the operator shell before dashboard build" "low"
        return
    }

    Write-ActionResult "node_env_check" "$version via $nodePath" "none" "none"
}

function Invoke-HistoryCleanupPreview {
    $historyRoot = Join-Path $Root "state\history"
    if (-not (Test-Path $historyRoot)) {
        Write-ActionResult "history_cleanup_preview" "history folder missing" "no cleanup needed" "none"
        return
    }

    $files = @(Get-ChildItem $historyRoot -Filter "control_plane_status_*.json" -File | Sort-Object LastWriteTimeUtc)
    $totalBytes = ($files | Measure-Object Length -Sum).Sum
    if ($null -eq $totalBytes) {
        $totalBytes = 0
    }
    $preview = "$($files.Count) snapshot(s), $totalBytes byte(s); no files deleted"
    $recommendation = if ($files.Count -gt 100) { "operator may archive old snapshots manually after review" } else { "none" }
    $risk = if ($files.Count -gt 100) { "low" } else { "none" }
    Write-ActionResult "history_cleanup_preview" $preview $recommendation $risk
}

function Invoke-ControlPlaneVerify {
    $validateScript = Join-Path $Root "scripts\validate_control_plane_snapshot.ps1"
    if (-not (Test-Path $validateScript)) {
        Write-ActionResult "control_plane_verify" "validator missing" "restore validate_control_plane_snapshot.ps1" "high"
        return
    }

    $validation = Invoke-SnapshotValidator -ValidateScript $validateScript
    if ($validation.ExitCode -eq 0) {
        Write-ActionResult "control_plane_verify" "snapshot validation passed: $($validation.Output)" "none" "none"
    }
    else {
        Write-ActionResult "control_plane_verify" "snapshot validation failed: $($validation.Output)" "fix schema/snapshot before UI handoff" "high"
    }
}

$actions = @(
    "repo_sync_check",
    "workspace_clean_check",
    "python_env_check",
    "node_env_check",
    "history_cleanup_preview",
    "control_plane_verify"
)

Write-Host ""
Write-Host "TDK Control Plane Operator Actions" -ForegroundColor Cyan
Write-Host "mode: read-only / preview"

$selectedActions = if ($Action -eq "all") { $actions } else { @($Action) }

foreach ($selectedAction in $selectedActions) {
    switch ($selectedAction) {
        "repo_sync_check" { Invoke-RepoSyncCheck }
        "workspace_clean_check" { Invoke-WorkspaceCleanCheck }
        "python_env_check" { Invoke-PythonEnvCheck }
        "node_env_check" { Invoke-NodeEnvCheck }
        "history_cleanup_preview" { Invoke-HistoryCleanupPreview }
        "control_plane_verify" { Invoke-ControlPlaneVerify }
    }
}

exit 0
