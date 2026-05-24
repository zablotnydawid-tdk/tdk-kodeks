from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs" / "local-audits"

HTTP_CHECKS = [
    ("Open WebUI", "http://127.0.0.1:3000/"),
    ("Ollama tags", "http://127.0.0.1:11434/api/tags"),
    ("KODEKS API", "http://127.0.0.1:8001/"),
    ("KODEKS Swagger", "http://127.0.0.1:8001/docs"),
    ("KODEKS Admin", "http://127.0.0.1:8001/admin/orders?admin_key=test-admin"),
    ("TDK backend health", "http://127.0.0.1:8010/health"),
    ("TDK backend Swagger", "http://127.0.0.1:8010/docs"),
    ("TDK frontend connected", "http://127.0.0.1:5174/"),
]

PORT_CHECKS = [
    ("Open WebUI", "127.0.0.1", 3000),
    ("Ollama", "127.0.0.1", 11434),
    ("KODEKS API", "127.0.0.1", 8001),
    ("TDK backend", "127.0.0.1", 8010),
    ("TDK frontend connected", "127.0.0.1", 5174),
    ("Redis", "127.0.0.1", 6379),
    ("Kafka", "127.0.0.1", 9092),
    ("Zookeeper", "127.0.0.1", 2181),
]


def ok_line(ok: bool, label: str, detail: str = "") -> str:
    status = "OK" if ok else "FAIL"
    if detail:
        return f"- [{status}] {label}: {detail}"
    return f"- [{status}] {label}"


def http_get(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "KODEKS-local-monitor"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(300)
            return 200 <= response.status < 400, f"HTTP {response.status}, {len(body)} bytes sample"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - monitor should report any local failure.
        return False, repr(exc)


def port_open(host: str, port: int, timeout: float = 1.0) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, f"{host}:{port}"
    except OSError as exc:
        return False, str(exc)


def run_command(command: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        return 127, str(exc)
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def ollama_models() -> list[str]:
    ok, detail = http_get("http://127.0.0.1:11434/api/tags")
    if not ok:
        return [f"unavailable: {detail}"]
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [model.get("name", "") for model in data.get("models", []) if model.get("name")]
    except Exception as exc:  # noqa: BLE001
        return [f"parse-error: {exc!r}"]


def build_report() -> tuple[bool, list[str]]:
    lines = [
        "# Local House Monitor",
        "",
        f"- Timestamp: {datetime.now().isoformat(timespec='seconds')}",
        f"- Root: {ROOT}",
        "",
        "## HTTP",
        "",
    ]

    results: list[bool] = []
    for label, url in HTTP_CHECKS:
        ok, detail = http_get(url)
        results.append(ok)
        lines.append(ok_line(ok, f"{label} ({url})", detail))

    lines.extend(["", "## Ports", ""])
    for label, host, port in PORT_CHECKS:
        ok, detail = port_open(host, port)
        results.append(ok)
        lines.append(ok_line(ok, label, detail))

    lines.extend(["", "## Ollama Models", ""])
    for model in ollama_models():
        lines.append(f"- {model}")

    lines.extend(["", "## KODEKS Operator Audit", ""])
    python = ROOT / ".venv" / "bin" / "python"
    audit_python = str(python if python.exists() else sys.executable)
    code, output = run_command([audit_python, "scripts/local_operator_audit.py", "--no-write"])
    audit_ok = code == 0 and "## Result\nPASS" in output
    results.append(audit_ok)
    lines.append(ok_line(audit_ok, "local_operator_audit.py --no-write"))
    if output:
        lines.append("")
        lines.append("```text")
        lines.extend(output.splitlines()[-12:])
        lines.append("```")

    lines.extend(["", "## Result", ""])
    success = all(results)
    lines.append("PASS" if success else "FAIL")
    return success, lines


def write_latest(lines: list[str]) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    output = AUDIT_DIR / "local_house_monitor_latest.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor local TDK/KODEKS house runtime.")
    parser.add_argument("--no-write", action="store_true", help="Do not write latest monitor report.")
    args = parser.parse_args()

    success, lines = build_report()
    if not args.no_write:
        output = write_latest(lines)
        lines.extend(["", f"Report written: {output}"])

    print("\n".join(lines))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
