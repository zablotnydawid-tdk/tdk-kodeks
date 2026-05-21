from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LEGACY_ROOT = Path("/mnt/c/Users/zablo/Desktop/AnchorGirdBESSCore")
LEGACY_SAFETY_ANCHORS = LEGACY_ROOT / "Nowy folder" / "safety_anchors.json"
LEGACY_BATTERY_ECONOMICS = LEGACY_ROOT / "battery_economics.json"
LEGACY_REASON_REGISTRY = LEGACY_ROOT / "Nowy folder" / "reason_registry.json"


@dataclass(frozen=True)
class SafetyAnchors:
    soc_min: float = 0.10
    soc_max: float = 0.90
    t_limit_c: float = 40.0
    max_c_rate_normal: float = 0.50
    max_c_rate_peak: float = 1.00
    tau_damped: float = 0.50
    tau_locked: float = 1.00
    safety_margin: float = 1.15


@dataclass(frozen=True)
class BatteryEconomics:
    capacity_mwh: float = 100.0
    battery_cost_pln: float = 220_000_000.0
    lifetime_cycles: float = 6000.0
    stress_high_c_rate: float = 1.5
    stress_high_temp: float = 1.3
    stress_deep_soc: float = 1.2


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def load_safety_anchors(path: Path = LEGACY_SAFETY_ANCHORS) -> SafetyAnchors:
    data = _read_json(path)
    policy = data.get("bess_anchor_policy_defaults", {})
    thresholds = data.get("tension_thresholds", {})
    return SafetyAnchors(
        soc_min=float(policy.get("soc_min", 0.10)),
        soc_max=float(policy.get("soc_max", 0.90)),
        t_limit_c=float(policy.get("t_limit_c", 40.0)),
        max_c_rate_normal=float(policy.get("max_c_rate_normal", 0.50)),
        max_c_rate_peak=float(policy.get("max_c_rate_peak", 1.00)),
        tau_damped=float(thresholds.get("tau_damped", 0.50)),
        tau_locked=float(thresholds.get("tau_locked", 1.00)),
    )


def load_battery_economics(path: Path = LEGACY_BATTERY_ECONOMICS) -> BatteryEconomics:
    data = _read_json(path)
    params = data.get("battery_params", {})
    stress = data.get("degradation_model", {}).get("stress_multiplier", {})
    return BatteryEconomics(
        capacity_mwh=float(params.get("capacity_mwh", 100.0)),
        battery_cost_pln=float(params.get("battery_cost_pln", 220_000_000.0)),
        lifetime_cycles=float(params.get("lifetime_cycles", 6000.0)),
        stress_high_c_rate=float(stress.get("high_c_rate", 1.5)),
        stress_high_temp=float(stress.get("high_temp", 1.3)),
        stress_deep_soc=float(stress.get("deep_soc", 1.2)),
    )


def load_reason_registry(path: Path = LEGACY_REASON_REGISTRY) -> dict[str, Any]:
    data = _read_json(path)
    return data.get("definitions", {})
