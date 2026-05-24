param(
    [switch]$IncludeInfra
)

$ErrorActionPreference = "Stop"

function Stop-PortProcess {
    param([int]$Port, [string]$Name)
    $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Host "[OK] $Name port $Port is already closed"
        return
    }

    foreach ($connection in $connections) {
        $pidToStop = $connection.OwningProcess
        if ($pidToStop -and $pidToStop -ne $PID) {
            Write-Host "[STOP] $Name port $Port pid $pidToStop"
            Stop-Process -Id $pidToStop -Force
        }
    }
}

Write-Host "=== TDK/KODEKS LOCAL HOUSE STOP ==="

Stop-PortProcess -Port 8001 -Name "KODEKS API"
Stop-PortProcess -Port 8010 -Name "TDK Backend"
Stop-PortProcess -Port 5174 -Name "TDK Frontend connected"

if ($IncludeInfra) {
    Stop-PortProcess -Port 5173 -Name "TDK Frontend default"
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker stop open-webui codexintrospect_lokalny_redis_1 codexintrospect_lokalny_kafka_1 codexintrospect_lokalny_zookeeper_1
    }
    Write-Host "[INFO] Infra stop requested. Ollama is not stopped by this script."
} else {
    Write-Host "[INFO] Docker/Open WebUI/Ollama left running. Use -IncludeInfra to stop Docker containers."
}
