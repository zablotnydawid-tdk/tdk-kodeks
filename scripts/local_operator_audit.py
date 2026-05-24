from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs" / "local-audits"


def run_command(command: list[str]) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        return 127, str(exc)

    output = "\n".join(
        part.strip()
        for part in (completed.stdout, completed.stderr)
        if part.strip()
    )
    return completed.returncode, output


def status_line(ok: bool, label: str, detail: str = "") -> str:
    prefix = "OK" if ok else "FAIL"
    if detail:
        return f"- [{prefix}] {label}: {detail}"
    return f"- [{prefix}] {label}"


def check_git_status(lines: list[str]) -> bool:
    code, output = run_command(["git", "status", "--short"])
    if code != 0:
        lines.append(status_line(False, "git status", output or "command failed"))
        return False

    changed = [line for line in output.splitlines() if line.strip()]
    detail = f"{len(changed)} changed paths" if changed else "clean"
    lines.append(status_line(True, "git status", detail))
    if changed:
        lines.append("")
        lines.append("Changed paths:")
        lines.extend(f"  {line}" for line in changed[:60])
        if len(changed) > 60:
            lines.append(f"  ... and {len(changed) - 60} more")
        lines.append("")
    return True


def check_py_compile(lines: list[str]) -> bool:
    files = [
        "app/engine/steps.py",
        "app/engine/process_engine.py",
        "app/output/report_builder.py",
    ]
    code, output = run_command([sys.executable, "-m", "py_compile", *files])
    ok = code == 0
    detail = ", ".join(files) if ok else output
    lines.append(status_line(ok, "py_compile core flow", detail))
    return ok


def check_pv_calculation(lines: list[str]) -> bool:
    sys.path.insert(0, str(ROOT))
    from app.engine.steps import calculate_energy_case

    result = calculate_energy_case(
        {
            "consumption_kwh": 2131,
            "price_per_kwh": 1.23,
            "pv_monthly_production_kwh": 4321,
        }
    )

    ok = (
        result is not None
        and result.get("cost_without_pv") == 2621.13
        and result.get("raw_cost_after_pv") == 0.0
        and result.get("residual_cost_floor") == 524.23
        and result.get("cost_after_pv") == 524.23
        and result.get("savings") == 2096.9
        and result.get("efficiency_label") == "wysoka efektywność"
        and result.get("calculation_mode") == "conservative_residual_estimate"
        and result.get("cost_after_pv") != 0
    )

    lines.append(status_line(ok, "PV conservative calculation", str(result)))
    return ok


def check_engine_to_report(lines: list[str]) -> bool:
    sys.path.insert(0, str(ROOT))
    from app.engine.process_engine import run_process
    from app.output.report_builder import build_report

    text = "Zuzycie 2131 kWh, cena 1.23 zl, PV 10 kWp, produkcja PV 4321 kWh"
    process_result = run_process(text.lower(), "CaseReporter")
    report = build_report(text, "CaseReporter", process_result)

    calculations = process_result.get("calculations") or {}
    required_line = "Szacowany koszt po kompensacji PV: 524.23"
    ok = (
        calculations.get("cost_after_pv") == 524.23
        and calculations.get("raw_cost_after_pv") == 0.0
        and required_line in report
        and "Szacowany koszt po kompensacji PV: 0" not in report
    )

    lines.append(
        status_line(
            ok,
            "engine -> report cost_after_pv",
            f"cost_after_pv={calculations.get('cost_after_pv')}",
        )
    )
    return ok


def check_pdf_kpi_if_available(lines: list[str]) -> bool:
    if importlib.util.find_spec("reportlab") is None:
        lines.append(status_line(True, "PDF KPI check", "skipped, reportlab not installed"))
        return True

    sys.path.insert(0, str(ROOT))
    from app.engine.process_engine import run_process
    from app.output.pdf_builder import _extract_kpis
    from app.output.report_builder import build_report

    text = "Zuzycie 2131 kWh, cena 1.23 zl, PV 10 kWp, produkcja PV 4321 kWh"
    process_result = run_process(text.lower(), "CaseReporter")
    report = build_report(text, "CaseReporter", process_result)
    kpis = _extract_kpis(report)
    ok = kpis.get("cost_after_pv") == "524.23 zł"
    lines.append(status_line(ok, "PDF KPI PO PV source", str(kpis)))
    return ok


def check_storage_dirs(lines: list[str]) -> bool:
    dirs = [
        ROOT / "data" / "orders",
        ROOT / "data" / "reports",
        ROOT / "docs",
    ]
    ok = True
    for directory in dirs:
        exists = directory.exists() and directory.is_dir()
        ok = ok and exists
        lines.append(status_line(exists, f"directory {directory.relative_to(ROOT)}"))
    return ok


def write_report(lines: list[str]) -> Path:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output = AUDIT_DIR / f"local_operator_audit_{timestamp}.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Local operator audit for KODEKS.")
    parser.add_argument("--no-write", action="store_true", help="Do not write markdown report.")
    args = parser.parse_args()

    lines = [
        "# Local Operator Audit",
        "",
        f"- Timestamp: {datetime.now().isoformat(timespec='seconds')}",
        f"- Root: {ROOT}",
        "",
        "## Checks",
        "",
    ]

    checks = [
        check_git_status,
        check_storage_dirs,
        check_py_compile,
        check_pv_calculation,
        check_engine_to_report,
        check_pdf_kpi_if_available,
    ]

    results = []
    for check in checks:
        try:
            results.append(check(lines))
        except Exception as exc:
            results.append(False)
            lines.append(status_line(False, check.__name__, repr(exc)))

    lines.append("")
    lines.append("## Result")
    success = all(results)
    lines.append("PASS" if success else "FAIL")

    report_path = None
    if not args.no_write:
        report_path = write_report(lines)
        lines.append("")
        lines.append(f"Report written: {report_path}")

    print("\n".join(lines))
    if report_path:
        print(f"\nREPORT_PATH={report_path}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
