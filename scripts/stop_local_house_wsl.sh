#!/usr/bin/env bash
set -euo pipefail

ROOT="/mnt/c/KODEKS"
LOG_DIR="$ROOT/logs/local-house"

stop_pid_file() {
  local name="$1"
  local pid_file="$LOG_DIR/${name}.pid"

  if [ ! -f "$pid_file" ]; then
    echo "[SKIP] No pid file for $name"
    return
  fi

  local pid
  pid="$(cat "$pid_file" || true)"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    echo "[STOP] $name pid $pid"
    kill "$pid" >/dev/null 2>&1 || true
  else
    echo "[OK] $name already stopped"
  fi
  rm -f "$pid_file"
}

echo "=== TDK/KODEKS LOCAL HOUSE STOP ==="
stop_pid_file "kodeks_api"
stop_pid_file "tdk_backend"
stop_pid_file "tdk_frontend"
echo "[INFO] Docker/Open WebUI/Ollama left running."
