$ErrorActionPreference = "Stop"

$KodeksRoot = "C:\KODEKS"
$TdkBackendRoot = "C:\TDK\TDK_backend"
$TdkFrontRoot = "C:\TDK\TDK_front"
$TdkBackendVenv = "C:\Users\$env:USERNAME\AppData\Local\Temp\tdk_backend_venv"

function Test-Port {
    param([int]$Port)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $client.Connect("127.0.0.1", $Port)
        $client.Close()
        return $true
    } catch {
        return $false
    }
}

function Start-IfPortClosed {
    param(
        [int]$Port,
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Command
    )

    if (Test-Port $Port) {
        Write-Host "[OK] $Name already listens on port $Port"
        return
    }

    Write-Host "[START] $Name on port $Port"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$WorkingDirectory'; $Command" | Out-Null
}

Write-Host "=== TDK/KODEKS LOCAL HOUSE START ==="

if (Get-Command docker -ErrorAction SilentlyContinue) {
    foreach ($container in @("open-webui", "codexintrospect_lokalny_redis_1", "codexintrospect_lokalny_kafka_1", "codexintrospect_lokalny_zookeeper_1")) {
        docker start $container *> $null
    }
    Write-Host "[OK] Docker containers requested"
} else {
    Write-Host "[WARN] Docker command not found"
}

if (-not (Test-Port 11434)) {
    Write-Host "[WARN] Ollama is not listening on 11434. Start Ollama from Windows if needed."
} else {
    Write-Host "[OK] Ollama listens on 11434"
}

if (-not (Test-Path "$KodeksRoot\.venv\Scripts\python.exe")) {
    Write-Host "[SETUP] Creating KODEKS .venv"
    py -3 -m venv "$KodeksRoot\.venv"
    & "$KodeksRoot\.venv\Scripts\python.exe" -m pip install -r "$KodeksRoot\requirements.txt"
}

Start-IfPortClosed -Port 8001 -Name "KODEKS API" -WorkingDirectory $KodeksRoot -Command "`$env:ADMIN_KEY='test-admin'; .\.venv\Scripts\python.exe -m uvicorn app.api.server:app --host 127.0.0.1 --port 8001"

if (-not (Test-Path "$TdkBackendVenv\Scripts\python.exe")) {
    Write-Host "[SETUP] Creating TDK backend temp venv"
    py -3 -m venv $TdkBackendVenv
    & "$TdkBackendVenv\Scripts\python.exe" -m pip install -r "$TdkBackendRoot\requirements.txt"
}

Start-IfPortClosed -Port 8010 -Name "TDK Backend" -WorkingDirectory $TdkBackendRoot -Command "`$env:PORT='8010'; '$TdkBackendVenv\Scripts\python.exe' main.py"

Start-IfPortClosed -Port 5174 -Name "TDK Frontend connected" -WorkingDirectory $TdkFrontRoot -Command "`$env:VITE_API_URL='http://127.0.0.1:8010'; npm run dev -- --host 127.0.0.1 --port 5174"

Write-Host ""
Write-Host "Open WebUI:      http://127.0.0.1:3000"
Write-Host "KODEKS API:      http://127.0.0.1:8001"
Write-Host "KODEKS Swagger:  http://127.0.0.1:8001/docs"
Write-Host "KODEKS Admin:    http://127.0.0.1:8001/admin/orders?admin_key=test-admin"
Write-Host "TDK Backend:     http://127.0.0.1:8010"
Write-Host "TDK Frontend:    http://127.0.0.1:5174"
Write-Host ""
Write-Host "Run monitor:"
Write-Host "cd C:\KODEKS; .\.venv\Scripts\python.exe .\scripts\local_house_status.py"
