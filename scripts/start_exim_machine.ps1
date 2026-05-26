param(
    [string]$Root = "C:\KODEKS",
    [string]$TdkRoot = "C:\TDK",
    [string]$EximRoot = "C:\EXIM"
)

$ErrorActionPreference = "Continue"

$KnownPorts = @(3000, 5173, 5174, 8000, 8001, 8010, 8787, 11434)

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
    Write-Host ("{0,-34} {1}" -f ($Key + ":"), $Value) -ForegroundColor $Color
}

function Get-CommandStatus {
    param(
        [string[]]$Candidates,
        [string]$VersionArgument = "--version"
    )
    foreach ($candidate in $Candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }
        if ($candidate -in @("node", "npm")) {
            return [pscustomobject]@{
                Name = $candidate
                Path = $command.Source
                Version = "present; version check skipped"
            }
        }
        $version = "present"
        try {
            if ($candidate -eq "py") {
                $version = (& $command.Source -3 --version 2>&1 | Select-Object -First 1)
            }
            else {
                $version = (& $command.Source $VersionArgument 2>&1 | Select-Object -First 1)
            }
        }
        catch {
            $version = "present; version UNKNOWN"
        }
        return [pscustomobject]@{
            Name = $candidate
            Path = $command.Source
            Version = [string]$version
        }
    }
    return $null
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

function Get-GitState {
    param([string]$Path)
    if (-not (Test-Path (Join-Path $Path ".git"))) {
        return [pscustomobject]@{
            Present = $false
            Branch = "UNKNOWN"
            Dirty = "UNKNOWN"
            Status = @()
        }
    }
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
        return [pscustomobject]@{
            Present = $true
            Branch = "UNKNOWN"
            Dirty = "UNKNOWN"
            Status = @("git command missing")
        }
    }
    $branch = "UNKNOWN"
    $status = @()
    try {
        $branch = (& $git.Source -C $Path rev-parse --abbrev-ref HEAD 2>$null)
        $status = @(& $git.Source -C $Path status --short 2>$null)
    }
    catch {
        $status = @("git status unavailable")
    }
    return [pscustomobject]@{
        Present = $true
        Branch = $branch
        Dirty = ($status.Count -gt 0)
        Status = $status
    }
}

function Get-PortState {
    param([int]$Port)
    try {
        $items = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
        if ($items.Count -gt 0) {
            return "listening"
        }
    }
    catch {
        return "UNKNOWN"
    }
    return "free"
}

function Test-Runtime {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Kind,
        [string]$StartHint,
        [int]$Port = 0
    )
    $present = Test-Path $Path
    $portState = "n/a"
    if ($Port -gt 0) {
        $portState = Get-PortState -Port $Port
    }
    return [pscustomobject]@{
        Name = $Name
        Kind = $Kind
        Path = $Path
        Present = $present
        Port = if ($Port -gt 0) { $Port } else { "n/a" }
        PortState = $portState
        StartHint = $StartHint
    }
}

function Write-RuntimeTable {
    param([array]$Items)
    foreach ($item in $Items) {
        $color = if ($item.Present) { "Green" } else { "Yellow" }
        Write-Kv $item.Name ("present={0}; kind={1}; port={2}; port_state={3}" -f $item.Present, $item.Kind, $item.Port, $item.PortState) $color
        Write-Host ("  path: {0}" -f $item.Path)
        Write-Host ("  start: {0}" -f $item.StartHint)
    }
}

$tdkFront = Join-Path $TdkRoot "TDK_front"
$tdkBackend = Join-Path $TdkRoot "TDK_backend"
$tdkPlatformNext = Join-Path $TdkRoot "TDK_platform_next"

$controlPlanePath = Join-Path $Root "state\control_plane_status.json"
$eximEntrypoint = Join-Path $Root "scripts\exim_operator_entrypoint.ps1"
$controlPlaneScript = Join-Path $Root "scripts\control_plane.ps1"
$liveCaseScript = Join-Path $Root "scripts\live_case_demo.ps1"
$operatorReviewScript = Join-Path $Root "scripts\operator_review_demo.ps1"
$acpcApiMain = Join-Path $Root "apps\api\main.py"
$acpcDb = Join-Path $Root "data\acpc.db"
$runApiBat = Join-Path $Root "run_api.bat"

$python = Get-CommandStatus -Candidates @("py", "python3", "python")
$node = Get-CommandStatus -Candidates @("node")
$npm = Get-CommandStatus -Candidates @("npm")
$gitState = Get-GitState -Path $Root
$controlPlane = Read-JsonFile -Path $controlPlanePath

$runtimes = @(
    Test-Runtime -Name "KODEKS runtime" -Path $Root -Kind "repo" -StartHint "cd C:\KODEKS; python main.py"
    Test-Runtime -Name "ACPC API foundation" -Path $acpcApiMain -Kind "fastapi/sqlite" -StartHint "C:\KODEKS\run_api.bat" -Port 8000
    Test-Runtime -Name "Control Plane" -Path $controlPlaneScript -Kind "operator snapshot" -StartHint "C:\KODEKS\scripts\control_plane.ps1"
    Test-Runtime -Name "EXIM Operator Entrypoint" -Path $eximEntrypoint -Kind "operator overview" -StartHint "C:\KODEKS\scripts\exim_operator_entrypoint.ps1"
    Test-Runtime -Name "Live Case Loop" -Path $liveCaseScript -Kind "local demo" -StartHint "C:\KODEKS\scripts\live_case_demo.ps1"
    Test-Runtime -Name "Operator Review Layer" -Path $operatorReviewScript -Kind "closed-case demo" -StartHint "C:\KODEKS\scripts\operator_review_demo.ps1"
    Test-Runtime -Name "ACPC diagnostics" -Path (Join-Path $Root "src\acpc\energy\pv_diagnostics") -Kind "python module" -StartHint "covered by ACPC API and tests"
    Test-Runtime -Name "TDK_backend" -Path (Join-Path $tdkBackend "main.py") -Kind "backend" -StartHint "cd C:\TDK\TDK_backend; python main.py" -Port 8010
    Test-Runtime -Name "TDK_front" -Path (Join-Path $tdkFront "package.json") -Kind "vite dashboard" -StartHint "cd C:\TDK\TDK_front; npm run dev -- --host 127.0.0.1 --port 5174" -Port 5174
    Test-Runtime -Name "TDK_platform_next" -Path (Join-Path $tdkPlatformNext "package.json") -Kind "next dashboard" -StartHint "cd C:\TDK\TDK_platform_next; npm run dev" -Port 3000
    Test-Runtime -Name "EXIM local root" -Path $EximRoot -Kind "runtime root" -StartHint "C:\EXIM\scripts\exim_operator_entrypoint.ps1"
    Test-Runtime -Name "Ollama local" -Path "C:\Users" -Kind "local model service" -StartHint "already external; verify http://127.0.0.1:11434/api/tags" -Port 11434
)

$missing = @()
if (-not $python) { $missing += "Python command missing" }
if (-not $node) { $missing += "Node command missing" }
if (-not $npm) { $missing += "NPM command missing" }
if (-not (Test-Path $controlPlanePath)) { $missing += "Control Plane snapshot missing" }
if (-not (Test-Path $acpcApiMain)) { $missing += "ACPC API main.py missing" }

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "        EXIM / ACPC MACHINE START REVIEW" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Kv "mode" "OBSERVE + VERIFY + RECOMMEND" "Green"
Write-Kv "auto start" "disabled" "Green"
Write-Kv "auto install" "disabled" "Green"
Write-Kv "auto fix" "disabled" "Green"

Write-Section "Toolchain"
Write-Kv "python" $(if ($python) { "$($python.Name) | $($python.Version)" } else { "UNKNOWN" }) $(if ($python) { "Green" } else { "Yellow" })
Write-Kv "node" $(if ($node) { $node.Version } else { "UNKNOWN" }) $(if ($node) { "Green" } else { "Yellow" })
Write-Kv "npm" $(if ($npm) { $npm.Version } else { "UNKNOWN" }) $(if ($npm) { "Green" } else { "Yellow" })

Write-Section "Repo State"
Write-Kv "root" $Root
Write-Kv "git present" $gitState.Present $(if ($gitState.Present) { "Green" } else { "Yellow" })
Write-Kv "branch" $gitState.Branch
Write-Kv "dirty" $gitState.Dirty $(if ($gitState.Dirty -eq $true) { "Yellow" } else { "Green" })
if ($gitState.Status.Count -gt 0) {
    foreach ($line in $gitState.Status | Select-Object -First 12) {
        Write-Host ("  {0}" -f $line) -ForegroundColor Yellow
    }
}

Write-Section "Control Plane Snapshot"
Write-Kv "snapshot" $(if (Test-Path $controlPlanePath) { "present" } else { "UNKNOWN" }) $(if (Test-Path $controlPlanePath) { "Green" } else { "Yellow" })
Write-Kv "generated_at" $controlPlane.generated_at
Write-Kv "workspace" $controlPlane.operator_context.workspace
if ($controlPlane.components) {
    Write-Kv "components" @($controlPlane.components.PSObject.Properties).Count "Green"
}
else {
    Write-Kv "components" "UNKNOWN"
}

Write-Section "SQLite / API State"
Write-Kv "ACPC API main" $(if (Test-Path $acpcApiMain) { "present" } else { "UNKNOWN" }) $(if (Test-Path $acpcApiMain) { "Green" } else { "Yellow" })
Write-Kv "run_api.bat" $(if (Test-Path $runApiBat) { "present" } else { "UNKNOWN" }) $(if (Test-Path $runApiBat) { "Green" } else { "Yellow" })
Write-Kv "data\acpc.db" $(if (Test-Path $acpcDb) { "present" } else { "UNKNOWN - will be created by API on first report" }) $(if (Test-Path $acpcDb) { "Green" } else { "Yellow" })
Write-Kv "port 8000" (Get-PortState -Port 8000)

Write-Section "Available Runtimes / APIs / Dashboards"
Write-RuntimeTable -Items $runtimes

Write-Section "Known Local Ports"
foreach ($port in $KnownPorts) {
    Write-Kv ("port {0}" -f $port) (Get-PortState -Port $port)
}

Write-Section "SAFE MODE Warnings"
if ($missing.Count -eq 0) {
    Write-Kv "blocking unknowns" "none" "Green"
}
else {
    foreach ($item in $missing) {
        Write-Kv "warning" $item "Yellow"
    }
}
if ($gitState.Dirty -eq $true) {
    Write-Kv "repo warning" "working tree has uncommitted changes; review before demo handoff" "Yellow"
}
Write-Kv "policy" "UNKNOWN instead of guessing; no auto-fix; no auto-install" "Green"

Write-Section "Recommended Startup Sequence"
Write-Host "1. Review repo state: git status --short"
Write-Host "2. Refresh Control Plane snapshot: C:\KODEKS\scripts\control_plane.ps1"
Write-Host "3. Open operator overview: C:\KODEKS\scripts\exim_operator_entrypoint.ps1"
Write-Host "4. Start ACPC API only if demo needs backend: C:\KODEKS\run_api.bat"
Write-Host "5. Verify API health: http://127.0.0.1:8000/health"
Write-Host "6. Run Live Case Loop demo if case proof is needed: C:\KODEKS\scripts\live_case_demo.ps1"
Write-Host "7. Run Operator Review demo to close case: C:\KODEKS\scripts\operator_review_demo.ps1"
Write-Host "8. Start one frontend only after backend target is known:"
Write-Host "   - TDK_front Vite: C:\TDK\TDK_front"
Write-Host "   - TDK_platform_next: C:\TDK\TDK_platform_next"
Write-Host "9. Keep TDK_backend separate unless its dependencies and port target are confirmed."

Write-Section "Demo Readiness"
$ready = @($runtimes | Where-Object { $_.Present -eq $true })
Write-Kv "detected systems" $ready.Count "Green"
Write-Kv "ready now" "Control Plane, EXIM entrypoint, ACPC API, Live Case Loop, Operator Review if dependencies are present" "Green"
Write-Kv "operator view" "what exists / what is running / what can start / what is demo-ready" "Green"
