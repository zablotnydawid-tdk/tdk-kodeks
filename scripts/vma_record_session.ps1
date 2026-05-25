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

$pythonCode = @'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
action = sys.argv[2]
session_path_arg = sys.argv[3]
user_input = sys.argv[4]
assistant_output = sys.argv[5]
event_type = sys.argv[6]
notes = sys.argv[7]
visual_reentry_required = sys.argv[8].lower() == "true"

if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from app.vma.session_recorder import (
    append_turn,
    create_session,
    finalize_session,
    load_session,
    save_report,
    save_session,
)

session_dir = root / "data" / "vma" / "sessions"
session_dir.mkdir(parents=True, exist_ok=True)

if action == "start":
    session = create_session(notes=notes)
    session_path = session_dir / f"{session['session_id']}.json"
    save_session(session, session_path)
    print(json.dumps({"session_path": str(session_path), "session_id": session["session_id"], "status": "started"}, sort_keys=True))
elif action == "add":
    if not session_path_arg:
        raise SystemExit("SessionPath is required for add")
    session_path = Path(session_path_arg)
    session = load_session(session_path)
    session = append_turn(
        session,
        user_input=user_input,
        assistant_output=assistant_output,
        event_type=event_type,
        notes=notes,
        visual_reentry_required=visual_reentry_required,
    )
    save_session(session, session_path)
    print(json.dumps({"session_path": str(session_path), "turns": len(session["turns"]), "status": "turn-added"}, sort_keys=True))
elif action == "finalize":
    if not session_path_arg:
        raise SystemExit("SessionPath is required for finalize")
    session_path = Path(session_path_arg)
    session = finalize_session(load_session(session_path))
    save_session(session, session_path)
    report_path = session_path.with_suffix(".md")
    save_report(session, report_path)
    print(json.dumps({
        "session_path": str(session_path),
        "report_path": str(report_path),
        "turns": len(session["turns"]),
        "continuity_score": session["continuity_metrics"].get("continuity_score"),
        "topology_retention_score": session["continuity_metrics"].get("topology_retention_score"),
        "recovery_efficiency": session["continuity_metrics"].get("recovery_efficiency"),
        "visual_reentry_required": session["continuity_metrics"].get("visual_reentry_required"),
        "first_real_user_continuity_win": session["first_real_user_continuity_win"],
        "status": "finalized",
    }, sort_keys=True))
'@

if (-not $SessionPath) {
    $SessionPathForPython = ""
}
else {
    $SessionPathForPython = [System.IO.Path]::GetFullPath($SessionPath)
}

try {
    if ($pythonCommand.Kind -eq "wsl") {
        $sessionArg = if ($SessionPathForPython) { Convert-ToWslPath $SessionPathForPython } else { "" }
        $output = & wsl.exe $pythonCommand.Path -c $pythonCode `
            (Convert-ToWslPath $Root) $Action $sessionArg $UserInput $AssistantOutput $EventType $Notes `
            ([string]$VisualReentryRequired.IsPresent).ToLowerInvariant() 2>&1
    }
    else {
        $output = & $pythonCommand.Path -c $pythonCode `
            $Root $Action $SessionPathForPython $UserInput $AssistantOutput $EventType $Notes `
            ([string]$VisualReentryRequired.IsPresent).ToLowerInvariant() 2>&1
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

