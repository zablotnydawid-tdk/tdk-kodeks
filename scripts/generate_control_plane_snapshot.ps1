param(
    [string]$Root = "C:\KODEKS",
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Continue"

function Exit-ControlledError {
    param([string]$Message)
    Write-Error $Message
    exit 1
}

function Exit-MissingDependency {
    param([string]$Message)
    Write-Error $Message
    exit 2
}

function Get-UtcNow {
    return (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
}

function Test-AnyPath {
    param([string[]]$Paths)
    foreach ($path in $Paths) {
        if (Test-Path $path) {
            return $true
        }
    }
    return $false
}

function Get-CommandVersion {
    param(
        [string[]]$Candidates,
        [string[]]$Arguments
    )

    $commandPath = Resolve-Executable -Candidates $Candidates
    if (-not $commandPath) {
        return ""
    }

    try {
        return ((& $commandPath @Arguments 2>$null | Select-Object -First 1) -as [string])
    }
    catch {
        return ""
    }
}

function Resolve-Executable {
    param([string[]]$Candidates)

    foreach ($candidate in $Candidates) {
        if (-not $candidate) {
            continue
        }
        if (Test-Path $candidate) {
            return $candidate
        }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return $command.Source
        }
    }
    return ""
}

function New-ComponentStatus {
    param(
        [string]$Name,
        [string]$Status,
        [string]$LastChecked,
        [string]$Source,
        [string]$Notes,
        [string]$DriftLevel,
        [string]$NextAction
    )

    return [ordered]@{
        name = $Name
        status = $Status
        last_checked = $LastChecked
        source = $Source
        notes = $Notes
        drift_level = $DriftLevel
        next_action = $NextAction
    }
}

function Get-AcpcReadOnlyStatus {
    param(
        [string]$Name,
        [string]$SourcePath,
        [string]$TestPath,
        [string]$SourceLabel,
        [string]$TestLabel,
        [string]$CheckedAt,
        [string]$InventoryPath
    )

    $sourcePresent = Test-Path $SourcePath
    $testsPresent = Test-Path $TestPath
    $lastTest = "last test result unavailable"

    if (Test-Path $InventoryPath) {
        try {
            $inventoryText = Get-Content -Raw -Path $InventoryPath
            if ($inventoryText -like "*PASS: 12 passed, 0 failed, 0 skipped*") {
                $lastTest = "ACPC fallback test result recorded: PASS: 12 passed, 0 failed, 0 skipped"
            }
        }
        catch {
            $lastTest = "last test result unreadable"
        }
    }

    if ($sourcePresent -and $testsPresent) {
        return New-ComponentStatus $Name "active" $CheckedAt "$SourceLabel; $TestLabel" "Read-only ACPC module and tests are present. $lastTest." "none" "none"
    }

    $missing = @()
    if (-not $sourcePresent) {
        $missing += $SourceLabel
    }
    if (-not $testsPresent) {
        $missing += $TestLabel
    }
    return New-ComponentStatus $Name "warning" $CheckedAt "$SourceLabel; $TestLabel" "Missing ACPC asset(s): $($missing -join ', '). $lastTest." "medium" "restore ACPC source/tests or rerun selective merge"
}

function Get-GitSnapshot {
    param([string]$Workspace)

    $gitPath = Resolve-Executable @(
        "git",
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe"
    )
    if (-not $gitPath) {
        return @{
            status = "error"
            drift = "high"
            notes = "git command is not available."
            next = "install git or run inside a Git-enabled shell"
            lastCommit = "unknown"
        }
    }

    $statusLines = @()
    $lastCommit = "unknown"
    $aheadBehind = ""
    $usedHeadFallback = $false
    try {
        $statusLines = @(& $gitPath -C $Workspace status --short 2>$null)
        $lastCommit = (& $gitPath -C $Workspace log --oneline -1 2>$null)
        if (-not $lastCommit) {
            $lastCommit = Get-GitHeadFallback -Workspace $Workspace
            $usedHeadFallback = $true
        }
        $aheadBehind = (& $gitPath -C $Workspace rev-list --left-right --count origin/main...HEAD 2>$null)
    }
    catch {
        return @{
            status = "error"
            drift = "high"
            notes = "Unable to read git status."
            next = "verify repository path and git configuration"
            lastCommit = "unknown"
        }
    }

    $dirty = $statusLines.Count -gt 0
    $ahead = 0
    $behind = 0
    if ($aheadBehind) {
        $parts = $aheadBehind -split "\s+"
        if ($parts.Count -ge 2) {
            [void][int]::TryParse($parts[0], [ref]$behind)
            [void][int]::TryParse($parts[1], [ref]$ahead)
        }
    }

    if ($dirty) {
        return @{
            status = "warning"
            drift = "medium"
            notes = "Working tree has $($statusLines.Count) pending change(s). Last commit: $lastCommit"
            next = "review git status before operator handoff"
            lastCommit = $lastCommit
        }
    }

    if ($ahead -gt 0) {
        return @{
            status = "warning"
            drift = "low"
            notes = "Repository is ahead of origin/main by $ahead commit(s). Last commit: $lastCommit"
            next = "push after operator review"
            lastCommit = $lastCommit
        }
    }

    if ($behind -gt 0) {
        return @{
            status = "warning"
            drift = "medium"
            notes = "Repository is behind origin/main by $behind commit(s). Last commit: $lastCommit"
            next = "pull or inspect remote changes before new work"
            lastCommit = $lastCommit
        }
    }

    if ($usedHeadFallback) {
        return @{
            status = "warning"
            drift = "low"
            notes = "Git command output was incomplete in this shell; HEAD fallback: $lastCommit"
            next = "run git status in the operator shell before push or handoff"
            lastCommit = $lastCommit
        }
    }

    return @{
        status = "active"
        drift = "none"
        notes = "Repository is clean and synchronized. Last commit: $lastCommit"
        next = "none"
        lastCommit = $lastCommit
    }
}

function Get-GitHeadFallback {
    param([string]$Workspace)

    $headPath = Join-Path $Workspace ".git\HEAD"
    if (-not (Test-Path $headPath)) {
        return "unknown"
    }

    $head = (Get-Content $headPath -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $head) {
        return "unknown"
    }
    if ($head -match "^ref:\s+(.+)$") {
        $refPath = Join-Path (Join-Path $Workspace ".git") $Matches[1]
        if (Test-Path $refPath) {
            $sha = (Get-Content $refPath -ErrorAction SilentlyContinue | Select-Object -First 1)
            if ($sha) {
                return "$($sha.Substring(0, 7)) current HEAD"
            }
        }
        return "unknown ref $($Matches[1])"
    }
    if ($head.Length -ge 7) {
        return "$($head.Substring(0, 7)) detached HEAD"
    }
    return "unknown"
}

if (-not $OutputPath) {
    $OutputPath = Join-Path $Root "state\control_plane_status.json"
}

try {
    if (-not (Test-Path $Root)) {
        Exit-MissingDependency "Workspace root missing: $Root"
    }

    $checkedAt = Get-UtcNow
    $stateRoot = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Force -Path $stateRoot -ErrorAction Stop | Out-Null

    $git = Get-GitSnapshot -Workspace $Root

    $axisPresent = Test-AnyPath @(
        (Join-Path $Root "app\final_axis\supervisor.py"),
        (Join-Path $Root "data\final_axis\runtime_log.jsonl")
    )
    $demonPresent = Test-AnyPath @(
        (Join-Path $Root "app\drift_energy_monitor\supervisor.py"),
        (Join-Path $Root "data\drift_energy_monitor\runtime_log.jsonl")
    )
    $anchorPresent = Test-AnyPath @(
        (Join-Path $Root "app\anchorgrid\engine.py"),
        (Join-Path $Root "tests\test_anchorgrid_engine.py")
    )
    $masterSyncPresent = Test-Path (Join-Path $Root "scripts\master_system_sync.ps1")
    $operatorStackPresent = Test-AnyPath @(
        (Join-Path $Root "scripts\start_local_house.ps1"),
        (Join-Path $Root "scripts\monitor_local_house.ps1"),
        (Join-Path $Root "docs\runbooks\local-operator-flow.md")
    )
    $liveCaseRequiredPaths = @(
        (Join-Path $Root "app\live_ops\live_case_loop.py"),
        (Join-Path $Root "scripts\live_case_demo.ps1"),
        (Join-Path $Root "sample_data\live_case_input.json"),
        (Join-Path $Root "docs\runbooks\live_case_demo.md")
    )
    $liveCaseMissing = @($liveCaseRequiredPaths | Where-Object { -not (Test-Path $_) })
    $liveCasePresent = $liveCaseMissing.Count -eq 0
    $liveCaseLastResult = Join-Path $Root "data\live_ops\live_case_result.json"
    $liveCaseLastResultPresent = Test-Path $liveCaseLastResult
    $workflowPresent = Test-AnyPath @(
        (Join-Path $Root "app\engine\process_engine.py"),
        (Join-Path $Root "app\output\report_builder.py")
    )
    $acpcInventoryPath = Join-Path $Root "docs\architecture\acpc_zip_inventory_compare.md"
    $acpcRuntimePath = Join-Path $Root "src\acpc\runtime"
    $acpcRuntimeTestsPath = Join-Path $Root "tests\runtime"
    $acpcIngestPath = Join-Path $Root "src\acpc\ingest"
    $acpcIngestTestsPath = Join-Path $Root "tests\ingest"
    $acpcPvDiagnosticsPath = Join-Path $Root "src\acpc\energy\pv_diagnostics"
    $acpcPvDiagnosticsTestsPath = Join-Path $Root "tests\energy"
    $blueprintPresent = Test-Path (Join-Path $Root "docs\blueprints\tdk_control_plane_ux.md")
    $masterMapPresent = Test-Path "C:\TDK_SYSTEM\FULL_SYSTEM_MAP.txt"

    $pythonVersion = Get-CommandVersion -Candidates @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        "python",
        "py"
    ) -Arguments @("--version")
    $nodeVersion = Get-CommandVersion -Candidates @(
        "node",
        "C:\Program Files\nodejs\node.exe"
    ) -Arguments @("--version")
    $pythonOk = -not [string]::IsNullOrWhiteSpace($pythonVersion)
    $nodeOk = -not [string]::IsNullOrWhiteSpace($nodeVersion)
    $wslPythonPresent = Test-Path (Join-Path $Root ".venv\bin\python")
    $packageJsonPresent = Test-Path (Join-Path $Root "package.json")

    $components = [ordered]@{
        axis_runtime = if ($axisPresent) {
            New-ComponentStatus "Final Axis Runtime" "active" $checkedAt "app/final_axis" "Final Axis runtime files or logs are present." "none" "none"
        }
        else {
            New-ComponentStatus "Final Axis Runtime" "error" $checkedAt "app/final_axis" "Final Axis runtime is missing." "high" "restore or generate Final Axis runtime"
        }

        demon_core = if ($demonPresent) {
            New-ComponentStatus "DRIFT_ENERGY_MONITOR / DEMON_CORE" "active" $checkedAt "app/drift_energy_monitor" "DEMON_CORE module or runtime log is present." "none" "none"
        }
        else {
            New-ComponentStatus "DRIFT_ENERGY_MONITOR / DEMON_CORE" "error" $checkedAt "app/drift_energy_monitor" "DEMON_CORE supervision layer is missing." "high" "restore DEMON_CORE module"
        }

        anchor_git = if ($anchorPresent) {
            New-ComponentStatus "Anchor Git / AnchorGrid" "active" $checkedAt "app/anchorgrid" "AnchorGrid module or test coverage is present." "none" "none"
        }
        else {
            New-ComponentStatus "Anchor Git / AnchorGrid" "unknown" $checkedAt "app/anchorgrid" "AnchorGrid presence could not be confirmed." "medium" "inspect AnchorGrid module and tests"
        }

        master_system_sync = if ($masterSyncPresent) {
            $note = if ($masterMapPresent) { "Master sync script and C:\TDK_SYSTEM map are present." } else { "Master sync script is present; C:\TDK_SYSTEM map has not been generated or is not visible." }
            $drift = if ($masterMapPresent) { "none" } else { "low" }
            $next = if ($masterMapPresent) { "none" } else { "run scripts/master_system_sync.ps1 when inventory is needed" }
            New-ComponentStatus "TDK Master System Sync" "active" $checkedAt "scripts/master_system_sync.ps1" $note $drift $next
        }
        else {
            New-ComponentStatus "TDK Master System Sync" "error" $checkedAt "scripts/master_system_sync.ps1" "Master System Sync script is missing." "high" "restore master_system_sync.ps1"
        }

        local_operator_stack = if ($operatorStackPresent) {
            New-ComponentStatus "Local Operator Stack" "active" $checkedAt "scripts/*local*; docs/runbooks/local-operator-flow.md" "Local start, monitor, backup, recovery or audit assets are present." "low" "run local operator audit before field handoff"
        }
        else {
            New-ComponentStatus "Local Operator Stack" "error" $checkedAt "scripts/*local*" "Local operator scripts are missing." "high" "restore Local Operator Stack"
        }

        live_case_loop = if ($liveCasePresent) {
            $note = if ($liveCaseLastResultPresent) { "LIVE CASE LOOP proof files are present; last demo result exists at data\live_ops\live_case_result.json." } else { "LIVE CASE LOOP proof files are present; no last demo runtime result found." }
            $drift = if ($liveCaseLastResultPresent) { "none" } else { "low" }
            New-ComponentStatus "LIVE CASE LOOP" "active" $checkedAt "app/live_ops/live_case_loop.py; scripts/live_case_demo.ps1" $note $drift "run scripts/live_case_demo.ps1 before field handoff"
        }
        else {
            $missingNames = @($liveCaseMissing | ForEach-Object { Resolve-Path -Path $_ -Relative -ErrorAction SilentlyContinue })
            if (-not $missingNames) {
                $missingNames = @($liveCaseMissing)
            }
            New-ComponentStatus "LIVE CASE LOOP" "warning" $checkedAt "app/live_ops/live_case_loop.py; scripts/live_case_demo.ps1; sample_data/live_case_input.json; docs/runbooks/live_case_demo.md" "Missing required proof asset(s): $($missingNames -join ', ')" "medium" "restore LIVE CASE LOOP proof files"
        }

        proservice_workflow = if ($workflowPresent) {
            New-ComponentStatus "ProService / TDK Workflow" "active" $checkedAt "app/engine/process_engine.py" "Process engine and report builder are available." "none" "none"
        }
        else {
            New-ComponentStatus "ProService / TDK Workflow" "error" $checkedAt "app/engine/process_engine.py" "Process workflow files are missing." "high" "restore process workflow modules"
        }

        acpc_runtime = Get-AcpcReadOnlyStatus "ACPC Runtime" $acpcRuntimePath $acpcRuntimeTestsPath "src/acpc/runtime" "tests/runtime" $checkedAt $acpcInventoryPath

        acpc_ingest_gateway = Get-AcpcReadOnlyStatus "ACPC Live Ingest Gateway" $acpcIngestPath $acpcIngestTestsPath "src/acpc/ingest" "tests/ingest" $checkedAt $acpcInventoryPath

        acpc_pv_diagnostics = Get-AcpcReadOnlyStatus "ACPC PV Diagnostics" $acpcPvDiagnosticsPath $acpcPvDiagnosticsTestsPath "src/acpc/energy/pv_diagnostics" "tests/energy" $checkedAt $acpcInventoryPath

        retina_dashboard = if ($blueprintPresent) {
            New-ComponentStatus "Retina Preview Layer" "unknown" $checkedAt "docs/blueprints/tdk_control_plane_ux.md" "Retina layer is blueprinted as read-only preview; dashboard not implemented." "none" "implement read-only preview after status contract stabilizes"
        }
        else {
            New-ComponentStatus "Retina Preview Layer" "unknown" $checkedAt "docs/blueprints/tdk_control_plane_ux.md" "Retina blueprint is missing." "medium" "restore or write Control Plane UX blueprint"
        }

        github_sync = New-ComponentStatus "GitHub Sync" $git.status $checkedAt "git status --short; git log --oneline -1" $git.notes $git.drift $git.next

        windows_environment = if ($pythonOk -and $nodeOk) {
            New-ComponentStatus "Windows Environment" "active" $checkedAt "python --version; node --version" "Python: $pythonVersion; Node: $nodeVersion" "none" "none"
        }
        elseif ($pythonOk -or $nodeOk -or $wslPythonPresent -or $packageJsonPresent) {
            $pythonNote = if ($pythonOk) { $pythonVersion } elseif ($wslPythonPresent) { "WSL/local .venv python present" } else { "not found" }
            $nodeNote = if ($nodeOk) { $nodeVersion } elseif ($packageJsonPresent) { "package.json present, node not visible to this shell" } else { "not found" }
            New-ComponentStatus "Windows Environment" "warning" $checkedAt "python --version; node --version; workspace runtime markers" "Python: $pythonNote; Node: $nodeNote" "medium" "expose missing runtime in Windows PATH if Control Plane runs in Windows shell"
        }
        else {
            New-ComponentStatus "Windows Environment" "error" $checkedAt "python --version; node --version" "Python and Node were not found in PATH." "high" "install or expose Python and Node in PATH"
        }
    }

    $snapshot = [ordered]@{
        schema_version = "1.0.0"
        generated_at = $checkedAt
        operator_context = [ordered]@{
            host = $env:COMPUTERNAME
            workspace = $Root
            runtime_mode = "local"
        }
        components = $components
    }

    $json = $snapshot | ConvertTo-Json -Depth 8
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($OutputPath, $json, $utf8NoBom)

    Write-Host "Control Plane status snapshot: $OutputPath"
    exit 0
}
catch {
    Exit-ControlledError "Control Plane snapshot generation failed: $($_.Exception.Message)"
}
