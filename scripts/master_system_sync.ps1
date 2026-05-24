param(
    [string]$Root = "C:\TDK_SYSTEM",
    [string[]]$ScanRoots = @("C:\KODEKS", "C:\TDK", "C:\WitnessAI", "$HOME\Desktop"),
    [switch]$FullDiskScan
)

$ErrorActionPreference = "Continue"

function Write-Step {
    param([string]$Message)
    Write-Host $Message
}

function Invoke-OptionalCommand {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$OutputPath
    )

    $tool = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $tool) {
        "Command not available: $Command" | Out-File -FilePath $OutputPath -Encoding utf8
        return
    }

    try {
        & $Command @Arguments 2>&1 | Out-File -FilePath $OutputPath -Encoding utf8
    }
    catch {
        "Command failed: $Command $($Arguments -join ' ')" | Out-File -FilePath $OutputPath -Encoding utf8
        $_ | Out-File -FilePath $OutputPath -Append -Encoding utf8
    }
}

function Get-ExistingScanRoots {
    param([string[]]$Roots)
    $Roots | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
}

function Find-GitRepositories {
    param([string[]]$Roots)

    foreach ($scanRoot in (Get-ExistingScanRoots $Roots)) {
        Get-ChildItem $scanRoot -Directory -Recurse -ErrorAction SilentlyContinue |
            Where-Object { Test-Path (Join-Path $_.FullName ".git") } |
            Select-Object @{Name = "Root"; Expression = { $scanRoot } }, FullName
    }
}

function Find-TdkModules {
    param([string[]]$Roots)

    foreach ($scanRoot in (Get-ExistingScanRoots $Roots)) {
        Get-ChildItem $scanRoot -Recurse -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -like "*DEMON*" -or
                $_.Name -like "*AXIS*" -or
                $_.Name -like "*ANCHOR*" -or
                $_.Name -like "*EXIM*" -or
                $_.Name -like "*Witness*"
            } |
            Select-Object @{Name = "Root"; Expression = { $scanRoot } }, FullName
    }
}

Write-Host ""
Write-Host "=============================================="
Write-Host "        TDK MASTER SYSTEM SYNC vXinf"
Write-Host "=============================================="
Write-Host ""

if ($FullDiskScan) {
    $ScanRoots = @("C:\")
    Write-Host "FULL DISK SCAN ENABLED. This may take time and may reveal private paths."
}

New-Item -ItemType Directory -Force -Path $Root | Out-Null
$Report = Join-Path $Root "FULL_SYSTEM_MAP.txt"

Write-Step "[1/9] SYSTEM SCAN..."
Invoke-OptionalCommand -Command "systeminfo" -Arguments @() -OutputPath (Join-Path $Root "systeminfo.txt")

Write-Step "[2/9] GITHUB / REPOS..."
Find-GitRepositories -Roots $ScanRoots |
    Sort-Object FullName |
    Out-File -FilePath (Join-Path $Root "git_repositories.txt") -Encoding utf8

Write-Step "[3/9] PYTHON ENV..."
Invoke-OptionalCommand -Command "python" -Arguments @("-m", "pip", "list") -OutputPath (Join-Path $Root "python_packages.txt")

Write-Step "[4/9] NODE / NPM..."
Invoke-OptionalCommand -Command "npm" -Arguments @("list", "-g", "--depth=0") -OutputPath (Join-Path $Root "node_global.txt")

Write-Step "[5/9] DOCKER..."
Invoke-OptionalCommand -Command "docker" -Arguments @("ps", "-a") -OutputPath (Join-Path $Root "docker_containers.txt")
Invoke-OptionalCommand -Command "docker" -Arguments @("images") -OutputPath (Join-Path $Root "docker_images.txt")

Write-Step "[6/9] SERVICES..."
Get-Service |
    Sort-Object Status, Name |
    Select-Object Status, Name, DisplayName |
    Out-File -FilePath (Join-Path $Root "windows_services.txt") -Encoding utf8

Write-Step "[7/9] STARTUP / AUTORUN..."
Get-CimInstance Win32_StartupCommand |
    Select-Object Name, Command, Location |
    Out-File -FilePath (Join-Path $Root "startup_apps.txt") -Encoding utf8

Write-Step "[8/9] DASHBOARD / WORKSPACE..."
if (Test-Path "$HOME\Desktop") {
    Get-ChildItem "$HOME\Desktop" |
        Select-Object Name, FullName, LastWriteTime |
        Out-File -FilePath (Join-Path $Root "desktop_layout.txt") -Encoding utf8
}
else {
    "Desktop path not found: $HOME\Desktop" | Out-File -FilePath (Join-Path $Root "desktop_layout.txt") -Encoding utf8
}

Write-Step "[9/9] DEMON / AXIS / ANCHOR / EXIM..."
Find-TdkModules -Roots $ScanRoots |
    Sort-Object FullName |
    Out-File -FilePath (Join-Path $Root "tdk_modules_detected.txt") -Encoding utf8

Write-Host ""
Write-Host "Generating unified report..."

@"
===========================================
TDK MASTER SYSTEM MAP
===========================================

Generated:
$(Get-Date)

Root:
$Root

Scan roots:
$($ScanRoots -join "`n")

FILES:
- systeminfo.txt
- git_repositories.txt
- python_packages.txt
- node_global.txt
- docker_containers.txt
- docker_images.txt
- windows_services.txt
- startup_apps.txt
- desktop_layout.txt
- tdk_modules_detected.txt

STATUS:
SYSTEM SYNCHRONIZED
DEMON_CORE: CHECK tdk_modules_detected.txt
GITWAY: CHECK git_repositories.txt
ANCHOR: CHECK tdk_modules_detected.txt
LOCAL STACK: CHECK git_repositories.txt AND desktop_layout.txt

NOTES:
- Default mode scans selected TDK/Witness workspace roots only.
- Use -FullDiskScan for full C:\ scan when you intentionally want a complete Windows map.
- This report avoids environment variable dumps and does not export secrets by design.

===========================================
"@ | Out-File -FilePath $Report -Encoding utf8

Write-Host ""
Write-Host "SYSTEM COMPLETE."
Write-Host "REPORT: $Report"
Write-Host ""
