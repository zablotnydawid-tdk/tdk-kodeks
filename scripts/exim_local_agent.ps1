param(
  [string]$Action = "help"
)

$Root = "C:\KODEKS"

function Header($t) {
  Write-Host ""
  Write-Host "=== $t ==="
}

switch ($Action) {

  "help" {
    Header "EXIM LOCAL AGENT"

    Write-Host ""
    Write-Host "AVAILABLE COMMANDS:"
    Write-Host ""

    Write-Host "status    -> machine/runtime overview"
    Write-Host "control   -> Control Plane"
    Write-Host "operator  -> EXIM Operator Entrypoint"
    Write-Host "api       -> start ACPC API"
    Write-Host "front     -> start TDK frontend"
    Write-Host "git       -> git status"

    Write-Host ""
    Write-Host "EXAMPLE:"
    Write-Host ".\scripts\exim_local_agent.ps1 status"
  }

  "status" {
    cd $Root
    .\scripts\start_exim_machine.ps1
  }

  "control" {
    cd $Root
    .\scripts\control_plane.ps1
  }

  "operator" {
    cd $Root
    .\scripts\exim_operator_entrypoint.ps1
  }

  "api" {
    cd "$Root\apps\api"
    python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
  }

  "front" {
    cd "C:\TDK\TDK_platform_next"
    npm run dev
  }

  "git" {
    cd $Root
    git status
  }

  default {
    Write-Host ""
    Write-Host "Unknown action: $Action"
    Write-Host "Run help:"
    Write-Host ".\scripts\exim_local_agent.ps1 help"
  }
}