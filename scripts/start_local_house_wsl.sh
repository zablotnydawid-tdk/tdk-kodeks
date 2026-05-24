#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/c/KODEKS"
TDK_BACKEND="/mnt/c/TDK/TDK_backend"
TDK_FRONT="/mnt/c/TDK/TDK_front"
TDK_BACKEND_VENV="/tmp/tdk_backend_venv"
LOG_DIR="$ROOT/logs/local-house"

mkdir -p "$LOG_DIR"

is_port_open() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket()
sock.settimeout(0.4)
try:
    sock.connect(("127.0.0.1", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}

start_background() {
  local name="$1"
  local port="$2"
  local cwd="$3"
  local command="$4"
  local log_file="$LOG_DIR/${name}.log"

  if is_port_open "$port"; then
    echo "[OK] $name already running on port $port"
    return
  fi

  echo "[START] $name on port $port"
  (
    cd "$cwd"
    nohup bash -lc "$command" > "$log_file" 2>&1 &
    echo "$!" > "$LOG_DIR/${name}.pid"
  )

  for _ in {1..40}; do
    if is_port_open "$port"; then
      echo "[OK] $name is ready on port $port"
      return
    fi
    sleep 0.5
  done

  echo "[WARN] $name did not confirm port $port yet. Check $log_file"
}

echo "=== TDK/KODEKS LOCAL HOUSE START ==="

if command -v docker >/dev/null 2>&1; then
  docker start open-webui codexintrospect_lokalny_redis_1 codexintrospect_lokalny_kafka_1 codexintrospect_lokalny_zookeeper_1 >/dev/null 2>&1 || true
  echo "[OK] Docker containers requested"
else
  echo "[WARN] Docker command not available in WSL"
fi

if is_port_open 11434; then
  echo "[OK] Ollama is running on 11434"
else
  echo "[WARN] Ollama is not running on 11434. Start Ollama from Windows if needed."
fi

if [ ! -x "$ROOT/.venv/bin/python" ]; then
  echo "[SETUP] Creating KODEKS .venv"
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt"
fi

start_background \
  "kodeks_api" \
  "8001" \
  "$ROOT" \
  "ADMIN_KEY=test-admin .venv/bin/python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8001"

if [ ! -x "$TDK_BACKEND_VENV/bin/python" ]; then
  echo "[SETUP] Creating TDK backend venv"
  python3 -m venv "$TDK_BACKEND_VENV"
  "$TDK_BACKEND_VENV/bin/python" -m pip install -r "$TDK_BACKEND/requirements.txt"
fi

start_background \
  "tdk_backend" \
  "8010" \
  "$TDK_BACKEND" \
  "PORT=8010 $TDK_BACKEND_VENV/bin/python main.py"

start_background \
  "tdk_frontend" \
  "5174" \
  "$TDK_FRONT" \
  "VITE_API_URL=http://127.0.0.1:8010 npm run dev -- --host 127.0.0.1 --port 5174"

echo ""
echo "=== LOCAL HOUSE URLS ==="
echo "Open WebUI:     http://127.0.0.1:3000"
echo "KODEKS:         http://127.0.0.1:8001"
echo "KODEKS Admin:   http://127.0.0.1:8001/admin/orders?admin_key=test-admin"
echo "TDK Frontend:   http://127.0.0.1:5174"
echo "TDK Backend:    http://127.0.0.1:8010"
echo ""

"$ROOT/.venv/bin/python" "$ROOT/scripts/local_house_status.py" || true
