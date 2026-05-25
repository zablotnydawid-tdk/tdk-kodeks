param(
    [string]$Root = "C:\KODEKS",
    [string]$SessionPath = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

if (-not $SessionPath) {
    $SessionPath = Join-Path $Root "sample_data\vma_continuity_session.json"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $Root "data\vma"
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
            $extension = [System.IO.Path]::GetExtension($candidate).ToLowerInvariant()
            if ($extension -eq ".exe") {
                return [pscustomobject]@{
                    Kind = "windows"
                    Path = $candidate
                }
            }
            continue
        }
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($command) {
            return [pscustomobject]@{
                Kind = "windows"
                Path = $command.Source
            }
        }
    }

    $wslPython = Join-Path $Root ".venv\bin\python"
    $wslCommand = Get-Command "wsl.exe" -ErrorAction SilentlyContinue
    if ((Test-Path $wslPython) -and $wslCommand) {
        return [pscustomobject]@{
            Kind = "wsl"
            Path = (Convert-ToWslPath $wslPython)
        }
    }

    return $null
}

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

$pythonCommand = Resolve-Python -Root $Root
if (-not $pythonCommand) {
    Write-Host "missing dependency: python" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path $SessionPath)) {
    Write-Host "missing sample session: $SessionPath" -ForegroundColor Red
    exit 2
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$reportJsonPath = Join-Path $OutputDir "vma_continuity_report.json"
$summaryMarkdownPath = Join-Path $OutputDir "vma_continuity_summary.md"
$statePath = Join-Path $OutputDir "vma_continuity_state.json"

$pythonCode = @'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
session_path = Path(sys.argv[2])
report_json_path = Path(sys.argv[3])
summary_markdown_path = Path(sys.argv[4])
state_path = Path(sys.argv[5])

if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.vma.runtime import process_session

session = json.loads(session_path.read_text(encoding="utf-8"))
report = process_session(session)
report_json_path.write_text(
    json.dumps(report["continuity_report_json"], indent=2, sort_keys=True),
    encoding="utf-8",
)
summary_markdown_path.write_text(
    report["continuity_summary_markdown"],
    encoding="utf-8",
)
state_path.write_text(
    json.dumps(report["continuity_state_update"], indent=2, sort_keys=True),
    encoding="utf-8",
)
print(json.dumps({
    "continuity_score": report["continuity_report_json"]["continuity_score"],
    "topology_retention_score": report["continuity_report_json"]["topology_retention_score"],
    "recovery_efficiency": report["continuity_report_json"]["recovery_efficiency"],
    "recursive_stability": report["continuity_report_json"]["recursive_stability"],
    "visual_reentry_required": report["continuity_report_json"]["visual_reentry_required"],
    "first_real_continuity_win": report["first_real_continuity_win"],
}, sort_keys=True))
'@

try {
    if ($pythonCommand.Kind -eq "wsl") {
        $pythonOutput = & wsl.exe $pythonCommand.Path -c $pythonCode `
            (Convert-ToWslPath $Root) `
            (Convert-ToWslPath $SessionPath) `
            (Convert-ToWslPath $reportJsonPath) `
            (Convert-ToWslPath $summaryMarkdownPath) `
            (Convert-ToWslPath $statePath) 2>&1
    }
    else {
        $pythonOutput = & $pythonCommand.Path -c $pythonCode $Root $SessionPath $reportJsonPath $summaryMarkdownPath $statePath 2>&1
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "VMA continuity benchmark failed" -ForegroundColor Red
        $pythonOutput | ForEach-Object { Write-Host $_ }
        exit 1
    }

    $resultJson = ($pythonOutput | Select-Object -Last 1)
    $result = $resultJson | ConvertFrom-Json
    $winStatus = if ($result.first_real_continuity_win) { "ACHIEVED" } else { "NOT_ACHIEVED" }
    $statusColor = if ($result.first_real_continuity_win) { "Green" } else { "Yellow" }

    Write-Host ""
    Write-Host "TDK VMA CONTINUITY BENCHMARK" -ForegroundColor Cyan
    Write-Host ("session: {0}" -f $SessionPath)
    Write-Host ("report_json: {0}" -f $reportJsonPath)
    Write-Host ("summary_markdown: {0}" -f $summaryMarkdownPath)
    Write-Host ("state_update: {0}" -f $statePath)
    Write-Host ""
    Write-Host ("continuity_score: {0}" -f $result.continuity_score)
    Write-Host ("topology_retention_score: {0}" -f $result.topology_retention_score)
    Write-Host ("recovery_efficiency: {0}" -f $result.recovery_efficiency)
    Write-Host ("recursive_stability: {0}" -f $result.recursive_stability)
    Write-Host ("visual_reentry_required: {0}" -f $result.visual_reentry_required)
    Write-Host ("FIRST_REAL_CONTINUITY_WIN: {0}" -f $winStatus) -ForegroundColor $statusColor
    Write-Host ""
    exit 0
}
catch {
    Write-Host "VMA continuity benchmark error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
