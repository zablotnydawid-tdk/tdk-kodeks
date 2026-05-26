
from __future__ import annotations
from typing import Any, Dict, List
from .models import Finding
from .normalization import parse_pl_number


def _num(v: Any) -> float:
    return parse_pl_number(v)


def evaluate_pv_rules(sample: Dict[str, Any], thermal_scan: Dict[str, Any] | None = None) -> List[Finding]:
    findings: List[Finding] = []

    daily = _num(sample.get("daily_yield_kwh", 0))
    expected = max(0.001, _num(sample.get("expected_yield_kwh", 0)))
    yield_drop_pct = max(0.0, (expected - daily) / expected * 100.0)

    strings = sample.get("strings", [])
    currents = [_num(s.get("current_a", 0)) for s in strings]
    powers = [_num(s.get("power_w", 0)) for s in strings]

    current_imbalance_pct = 0.0
    if len(currents) >= 2 and max(currents) > 0:
        current_imbalance_pct = (max(currents) - min(currents)) / max(currents) * 100.0

    insulation = _num(sample.get("insulation_mohm", 999))
    module_temp = _num(sample.get("module_temperature_c", 0))

    if yield_drop_pct > 15.0:
        findings.append(Finding(
            id="yield_drop",
            severity="warning",
            diagnosis="spadek uzysku",
            recommendation="porownaj stringi, pogode i zacienienie",
            evidence={"yield_drop_pct": round(yield_drop_pct, 2), "daily_yield_kwh": daily, "expected_yield_kwh": expected},
        ))

    if insulation < 2.0 and yield_drop_pct > 15.0:
        findings.append(Finding(
            id="pid_risk",
            severity="critical",
            diagnosis="podejrzenie PID",
            recommendation="wykonaj test izolacji i pomiar EL",
            evidence={"insulation_mohm": insulation, "yield_drop_pct": round(yield_drop_pct, 2)},
        ))

    if current_imbalance_pct > 20.0:
        findings.append(Finding(
            id="mpi_risk",
            severity="warning",
            diagnosis="podejrzenie MPI lub niedopasowania modulow",
            recommendation="sprawdz polaczenia, zacienienie i charakterystyke I-V",
            evidence={"current_imbalance_pct": round(current_imbalance_pct, 2), "currents_a": currents, "powers_w": powers},
        ))

    # MVP: if no thermal image baseline exists, high module temp is treated as hotspot risk.
    temp_delta = None
    if thermal_scan:
        temp_delta = _num(thermal_scan.get("max_delta_c", 0))
    elif module_temp >= 70.0:
        temp_delta = 15.0

    if temp_delta is not None and temp_delta >= 15.0:
        findings.append(Finding(
            id="hotspot",
            severity="critical",
            diagnosis="hot spot",
            recommendation="odlacz string i wykonaj inspekcje termowizyjna",
            evidence={"module_temperature_c": module_temp, "thermal_delta_c": temp_delta},
        ))

    return findings
