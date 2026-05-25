param(
    [ValidateSet("start", "add", "finalize")]
    [string]$Action = "start",
    [string]$Root = "C:\KODEKS",
    [string]$SessionPath = "",
    [string]$UserInput = "",
    [string]$AssistantOutput = "",
    [ValidateSet("turn", "interruption", "recovery_attempt")]
    [string]$EventType = "turn",
    [string]$Notes = "",
    [switch]$VisualReentryRequired
)

$ErrorActionPreference = "Stop"

function Convert-ToWslPath {
    param([string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if ($fullPath -match "^([A-Za-z]):\\(.*)$") {
        $drive = $Matches[1].ToLowerInvariant()
        $rest = $Matches[2] -replace "\\", "/"
        return "/mnt/$drive/$rest"
    }
    return $Path
}

function Resolve-Python {
    param([string]$Root)

    $candidates = @(
        (Join-Path $Root ".venv\Scripts\python.exe"),
        "python",
        "py"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            if ([System.IO.Path]::GetExtension($candidate).ToLowerInvariant() -eq ".exe") {
                return [pscustomobject]@{ Kind = "windows"; Path = $candidate }
            }
            continue
        }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return [pscustomobject]@{ Kind = "windows"; Path = $command.Source }
        }
    }

    $wslPython = Join-Path $Root ".venv\bin\python"
    if ((Test-Path $wslPython) -and (Get-Command "wsl.exe" -ErrorAction SilentlyContinue)) {
        return [pscustomobject]@{ Kind = "wsl"; Path = (Convert-ToWslPath $wslPython) }
    }
    return $null
}

$pythonCommand = Resolve-Python -Root $Root
if (-not $pythonCommand) {
    Write-Host "missing dependency: python" -ForegroundColor Red
    exit 2
}

if (-not $SessionPath) {
    $SessionPathForPython = ""
}
else {
    $SessionPathForPython = [System.IO.Path]::GetFullPath($SessionPath)
}

$helperPath = Join-Path $Root "scripts\vma_record_session.py"
if (-not (Test-Path $helperPath)) {
    Write-Host "missing helper: $helperPath" -ForegroundColor Red
    exit 2
}

$arguments = @(
    $Action,
    "--root", $Root,
    "--event-type", $EventType
)
if ($SessionPathForPython) {
    $arguments += @("--session-path", $SessionPathForPython)
}
if ($UserInput) {
    $arguments += @("--user-input", $UserInput)
}
if ($AssistantOutput) {
    $arguments += @("--assistant-output", $AssistantOutput)
}
if ($Notes) {
    $arguments += @("--notes", $Notes)
}
if ($VisualReentryRequired.IsPresent) {
    $arguments += "--visual-reentry-required"
}

try {
    if ($pythonCommand.Kind -eq "wsl") {
        $wslArgs = @((Convert-ToWslPath $helperPath))
        foreach ($argument in $arguments) {
            if ($argument -eq $Root) {
                $wslArgs += (Convert-ToWslPath $Root)
            }
            elseif ($argument -eq $SessionPathForPython) {
                $wslArgs += (Convert-ToWslPath $SessionPathForPython)
            }
            else {
                $wslArgs += $argument
            }
        }
        $output = & wsl.exe $pythonCommand.Path @wslArgs 2>&1
    }
    else {
        $output = & $pythonCommand.Path $helperPath @arguments 2>&1
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "VMA session recorder failed" -ForegroundColor Red
        $output | ForEach-Object { Write-Host $_ }
        exit 1
    }

    $result = ($output | Select-Object -Last 1) | ConvertFrom-Json
    Write-Host ""
    Write-Host "TDK VMA REAL USER SESSION" -ForegroundColor Cyan
    Write-Host ("status: {0}" -f $result.status)
    Write-Host ("session_path: {0}" -f $result.session_path)
    if ($result.PSObject.Properties.Name -contains "turns") {
        Write-Host ("turns: {0}" -f $result.turns)
    }
    if ($result.PSObject.Properties.Name -contains "report_path") {
        Write-Host ("report_path: {0}" -f $result.report_path)
        Write-Host ("continuity_score: {0}" -f $result.continuity_score)
        Write-Host ("topology_retention_score: {0}" -f $result.topology_retention_score)
        Write-Host ("recovery_efficiency: {0}" -f $result.recovery_efficiency)
        Write-Host ("visual_reentry_required: {0}" -f $result.visual_reentry_required)
        $win = if ($result.first_real_user_continuity_win) { "ACHIEVED" } else { "NOT_ACHIEVED" }
        Write-Host ("FIRST_REAL_USER_CONTINUITY_WIN: {0}" -f $win) -ForegroundColor $(if ($result.first_real_user_continuity_win) { "Green" } else { "Yellow" })
    }
    Write-Host ""
    exit 0
}
catch {
    Write-Host "VMA session recorder error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
