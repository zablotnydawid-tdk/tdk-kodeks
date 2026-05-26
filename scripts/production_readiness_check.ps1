param(
    [string]$Root = "C:\KODEKS",
    [string]$TdkRoot = "C:\TDK"
)

$ErrorActionPreference = "Continue"

$Ports = @(80, 443, 8000, 3000, 5174)

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
    Write-Host ("{0,-36} {1}" -f ($Key + ":"), $Value) -ForegroundColor $Color
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

function Test-PathStatus {
    param([string]$Path)
    if (Test-Path $Path) {
        return "present"
    }
    return "UNKNOWN"
}

function Test-GitIgnore {
    param([string]$Pattern)
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        try {
            $output = & $git.Source -C $Root check-ignore -v $Pattern 2>$null
            if ($LASTEXITCODE -eq 0 -and $output) {
                return "ignored"
            }
        }
        catch {
            return "UNKNOWN"
        }
    }

    $gitignore = Join-Path $Root ".gitignore"
    if (-not (Test-Path $gitignore)) {
        return "UNKNOWN - .gitignore missing"
    }
    $rules = @(Get-Content -Path $gitignore | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.Trim().StartsWith("#") })
    foreach ($rule in $rules) {
        $clean = $rule.Trim()
        if ($clean.EndsWith("/") -and $Pattern.StartsWith($clean)) {
            return "ignored"
        }
        if ($clean.Contains("*")) {
            $regex = "^" + [regex]::Escape($clean).Replace("\*", ".*") + "$"
            if ($Pattern -match $regex) {
                return "ignored"
            }
        }
        elseif ($Pattern -eq $clean) {
            return "ignored"
        }
    }
    return "NOT_IGNORED"
}

function Test-PublicControlPlaneMarker {
    $paths = @(
        (Join-Path $Root "apps\web"),
        (Join-Path $Root "apps\api")
    )
    $publicHits = @()
    foreach ($path in $paths) {
        if (-not (Test-Path $path)) {
            continue
        }
        try {
            $hits = Select-String -Path (Join-Path $path "*") -Pattern "control_plane_status|Control Plane|DEMON|VMA|EXIM Operator" -Recurse -ErrorAction SilentlyContinue
            $publicHits += @($hits)
        }
        catch {
            continue
        }
    }
    if ($publicHits.Count -gt 0) {
        return "REVIEW_REQUIRED"
    }
    return "not_public"
}

$acpcApi = Join-Path $Root "apps\api\main.py"
$runApi = Join-Path $Root "run_api.bat"
$tdkFront = Join-Path $TdkRoot "TDK_front"
$tdkPlatformNext = Join-Path $TdkRoot "TDK_platform_next"
$appsWeb = Join-Path $Root "apps\web"
$operatorReview = Join-Path $Root "app\live_ops\operator_review.py"
$architectureDoc = Join-Path $Root "docs\architecture\tdkproservice_production_entrypoint.md"
$deployRunbook = Join-Path $Root "docs\runbooks\tdkproservice_domain_deploy.md"
$safetyRunbook = Join-Path $Root "docs\runbooks\production_safety_boundary.md"

$missingDecisions = @(
    "hosting",
    "DNS",
    "SSL",
    "mail",
    "storage",
    "backup",
    "log retention"
)

$checks = @(
    [pscustomobject]@{ Name = "ACPC API"; Status = Test-PathStatus $acpcApi; Required = $true },
    [pscustomobject]@{ Name = "run_api.bat"; Status = Test-PathStatus $runApi; Required = $true },
    [pscustomobject]@{ Name = "TDK_front"; Status = Test-PathStatus $tdkFront; Required = $false },
    [pscustomobject]@{ Name = "TDK_platform_next"; Status = Test-PathStatus $tdkPlatformNext; Required = $false },
    [pscustomobject]@{ Name = "apps/web"; Status = Test-PathStatus $appsWeb; Required = $false },
    [pscustomobject]@{ Name = "Operator Review"; Status = Test-PathStatus $operatorReview; Required = $true },
    [pscustomobject]@{ Name = "Architecture doc"; Status = Test-PathStatus $architectureDoc; Required = $true },
    [pscustomobject]@{ Name = "Domain deploy runbook"; Status = Test-PathStatus $deployRunbook; Required = $true },
    [pscustomobject]@{ Name = "Safety boundary runbook"; Status = Test-PathStatus $safetyRunbook; Required = $true }
)

$runtimeIgnore = @(
    [pscustomobject]@{ Path = "data/acpc.db"; Status = Test-GitIgnore "data/acpc.db" },
    [pscustomobject]@{ Path = "data/uploads/example.csv"; Status = Test-GitIgnore "data/uploads/example.csv" },
    [pscustomobject]@{ Path = "data/reports/example.json"; Status = Test-GitIgnore "data/reports/example.json" },
    [pscustomobject]@{ Path = "data/reports/example.md"; Status = Test-GitIgnore "data/reports/example.md" },
    [pscustomobject]@{ Path = "data/live_ops/example.json"; Status = Test-GitIgnore "data/live_ops/example.json" }
)

$publicControlPlane = Test-PublicControlPlaneMarker
$requiredUnknown = @($checks | Where-Object { $_.Required -eq $true -and $_.Status -ne "present" })
$ignoreFailures = @($runtimeIgnore | Where-Object { $_.Status -ne "ignored" })

$status = "READY_FOR_LOCAL_PRODUCTION_PLANNING"
if ($requiredUnknown.Count -gt 0 -or $ignoreFailures.Count -gt 0 -or $publicControlPlane -ne "not_public") {
    $status = "NOT_READY_REVIEW_REQUIRED"
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   TDKPROSERVICE PRODUCTION READINESS CHECK" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Kv "mode" "OBSERVE + VERIFY + RECOMMEND" "Green"
Write-Kv "deploy" "disabled" "Green"
Write-Kv "auto start" "disabled" "Green"
Write-Kv "auto install" "disabled" "Green"
Write-Kv "DNS changes" "disabled" "Green"

Write-Section "Production Readiness Status"
Write-Kv "status" $status $(if ($status -eq "READY_FOR_LOCAL_PRODUCTION_PLANNING") { "Green" } else { "Yellow" })

Write-Section "Required / Candidate Systems"
foreach ($check in $checks) {
    $color = if ($check.Status -eq "present") { "Green" } elseif ($check.Required) { "Yellow" } else { "Gray" }
    Write-Kv $check.Name $check.Status $color
}

Write-Section "Public Ports"
foreach ($port in $Ports) {
    Write-Kv ("port {0}" -f $port) (Get-PortState -Port $port)
}

Write-Section "Runtime Data Git Boundary"
foreach ($item in $runtimeIgnore) {
    Write-Kv $item.Path $item.Status $(if ($item.Status -eq "ignored") { "Green" } else { "Yellow" })
}

Write-Section "Private Runtime Boundary"
Write-Kv "Control Plane public marker" $publicControlPlane $(if ($publicControlPlane -eq "not_public") { "Green" } else { "Yellow" })
Write-Kv "public Control Plane" "forbidden" "Green"
Write-Kv "public DEMON log" "forbidden" "Green"
Write-Kv "public runtime state" "forbidden" "Green"
Write-Kv "autonomous decisions" "forbidden" "Green"

Write-Section "Missing Decisions"
foreach ($decision in $missingDecisions) {
    Write-Kv $decision "requires operator confirmation" "Yellow"
}

Write-Section "Recommended Next Step"
if ($status -eq "READY_FOR_LOCAL_PRODUCTION_PLANNING") {
    Write-Host "Choose hosting/DNS/SSL/mail/storage decisions, then stage a restricted public frontend for tdkproservice.pl."
}
else {
    Write-Host "Resolve review-required checks before domain staging. Keep EXIM/Control Plane private."
}
