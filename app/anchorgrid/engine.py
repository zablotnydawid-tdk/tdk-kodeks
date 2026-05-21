from __future__ import annotations

import math

from app.anchorgrid.config import (
    LEGACY_BATTERY_ECONOMICS,
    LEGACY_REASON_REGISTRY,
    LEGACY_SAFETY_ANCHORS,
    load_battery_economics,
    load_reason_registry,
    load_safety_anchors,
)
from app.anchorgrid.schemas import AnchorGridResult, BessInput


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _normalize_soc(soc: float) -> float:
    if soc > 1:
        return _clamp(soc / 100, 0, 1)
    return _clamp(soc, 0, 1)


def _format_c_rate(value: float) -> str:
    if value <= 0:
        return "0.0C"
    return f"okolo {value:.2g}C"


def _thermal_limit(t_cell: float, t_amb: float, hvac: bool) -> tuple[float, str, list[str]]:
    warnings: list[str] = []

    if t_cell >= 55:
        return 0.0, "critical", ["temperatura ogniw krytyczna"]
    if t_cell >= 48:
        warnings.append("temperatura ogniw bardzo wysoka")
        safe_u = 0.2
        margin = "critical"
    elif t_cell >= 42:
        warnings.append("temperatura ogniw podwyzszona")
        safe_u = 0.3
        margin = "niski"
    elif t_cell >= 38:
        warnings.append("temperatura ogniw podwyzszona")
        safe_u = 0.5
        margin = "niski"
    elif t_cell >= 34:
        safe_u = 0.7
        margin = "sredni"
    else:
        safe_u = 1.0
        margin = "wysoki"

    if t_amb >= 35:
        warnings.append("wysoka temperatura otoczenia")
        safe_u -= 0.2
    elif t_amb >= 30:
        warnings.append("temperatura otoczenia podwyzszona")
        safe_u -= 0.1

    if hvac:
        safe_u += 0.1
    else:
        warnings.append("HVAC nieaktywny")
        safe_u -= 0.1

    safe_u = round(_clamp(safe_u, 0, 1.2), 2)
    if safe_u <= 0.25:
        margin = "critical"
    elif safe_u <= 0.55 and margin == "wysoki":
        margin = "niski"

    return safe_u, margin, warnings


def _market_impulse(price: float | None, avg: float | None, std: float | None, profile: str) -> float:
    if price is None:
        return 0.35
    avg = 700.0 if avg is None else avg
    std = max(1e-6, 300.0 if std is None else std)
    z_score = _clamp((price - avg) / std, -5, 5)
    intensity = 1 / (1 + math.exp(-z_score))
    profile = profile.upper().strip()
    if profile == "SAFETY_FIRST":
        return 0.6 * intensity
    if profile == "GRID_FIRST":
        return 0.8 * intensity
    return intensity


def _tension(
    requested_u: float,
    predicted_max_temp: float,
    soc_end: float,
    forecast_confidence_score: float,
    data: BessInput,
) -> float:
    anchors = load_safety_anchors()
    thermal_pressure = max(0, predicted_max_temp / max(anchors.t_limit_c, 1))
    soc_pressure = 0.0
    if soc_end < anchors.soc_min:
        soc_pressure = (anchors.soc_min - soc_end) / max(anchors.soc_min, 0.01)
    elif soc_end > anchors.soc_max:
        soc_pressure = (soc_end - anchors.soc_max) / max(1 - anchors.soc_max, 0.01)

    c_rate_pressure = max(0, requested_u / max(anchors.max_c_rate_normal, 0.01) - 1)
    uncertainty_pressure = 1 - _clamp(forecast_confidence_score, 0, 1)
    market_pressure = _market_impulse(data.price, data.avg_24h_price, data.std_24h_price, data.profile)

    raw = (
        0.38 * thermal_pressure
        + 0.24 * c_rate_pressure
        + 0.18 * soc_pressure
        + 0.12 * uncertainty_pressure
        + 0.08 * market_pressure
    )
    return round(_clamp(raw, 0, 2), 3)


def _economics(requested_u: float, predicted_max_temp: float, soc_end: float, horizon_minutes: int, price: float | None) -> dict:
    econ = load_battery_economics()
    horizon_h = horizon_minutes / 60
    price_pln_mwh = 0.0 if price is None else price
    energy_mwh = econ.capacity_mwh * requested_u * horizon_h
    revenue = energy_mwh * price_pln_mwh

    base_cycle_cost = econ.battery_cost_pln / max(econ.lifetime_cycles, 1)
    throughput_fraction = _clamp(requested_u * horizon_h, 0, 1)
    stress = 1.0
    if requested_u > 0.7:
        stress *= econ.stress_high_c_rate
    if predicted_max_temp > 35:
        stress *= econ.stress_high_temp
    anchors = load_safety_anchors()
    if soc_end < anchors.soc_min + 0.05 or soc_end > anchors.soc_max - 0.05:
        stress *= econ.stress_deep_soc

    degradation_cost = base_cycle_cost * throughput_fraction * stress
    return {
        "revenue_pln": round(revenue, 2),
        "degradation_cost_pln": round(degradation_cost, 2),
        "net_value_pln": round(revenue - degradation_cost, 2),
        "stress_multiplier": round(stress, 3),
    }


def _reason_detail(code: str, message: str) -> dict:
    registry = load_reason_registry()
    meta = registry.get(code, {})
    return {
        "code": code,
        "message": message,
        "severity": meta.get("severity", "INFO"),
        "action": meta.get("action", "MONITOR"),
        "label_pl": meta.get("label_pl", code),
        "desc_pl": meta.get("desc_pl", message),
    }


def _soc_limited_u(
    safe_u: float,
    soc: float,
    direction: str,
    warnings: list[str],
) -> tuple[float, bool]:
    blocked = False
    if direction == "DISCHARGE":
        if soc <= 0.08:
            warnings.append("SoC zbyt niski do rozladowania")
            return 0.0, True
        if soc <= 0.2:
            warnings.append("niski SoC, ograniczyc moc rozladowania")
            safe_u = min(safe_u, 0.3)
    elif direction == "CHARGE":
        if soc >= 0.97:
            warnings.append("SoC zbyt wysoki do ladowania")
            return 0.0, True
        if soc >= 0.85:
            warnings.append("wysoki SoC, ograniczyc moc ladowania")
            safe_u = min(safe_u, 0.3)
    else:
        warnings.append("nieznany kierunek operacji")
        return 0.0, True

    return round(_clamp(safe_u, 0, 1.2), 2), blocked


def _project_soc(soc: float, safe_u: float, direction: str, horizon_minutes: int) -> float:
    horizon_hours = max(horizon_minutes, 0) / 60
    delta = safe_u * horizon_hours
    if direction == "CHARGE":
        return _clamp(soc + delta, 0, 1)
    return _clamp(soc - delta, 0, 1)


def _predict_max_temp(t_cell: float, t_amb: float, requested_u: float, hvac: bool, horizon_minutes: int) -> float:
    horizon_factor = _clamp(horizon_minutes / 15, 0.25, 4)
    c_rate_heat = (requested_u**2) * 3.8 * horizon_factor
    ambient_heat = max(t_amb - 25, 0) * 0.12 * horizon_factor
    hvac_cooling = 1.2 * horizon_factor if hvac else 0
    return round(max(t_cell, t_cell + c_rate_heat + ambient_heat - hvac_cooling), 1)


def _forecast_confidence(horizon_minutes: int, t_cell: float, t_amb: float, requested_u: float) -> tuple[float, str]:
    if horizon_minutes <= 15 and requested_u <= 0.8 and t_cell < 45 and t_amb < 35:
        return 0.85, "HIGH"
    if horizon_minutes <= 60 and requested_u <= 1.0 and t_cell < 50:
        return 0.65, "MEDIUM"
    return 0.4, "LOW"


def _degradation_stress(t_cell: float, predicted_max_temp: float, requested_u: float, safe_limit_u: float) -> str:
    if predicted_max_temp >= 48 or t_cell >= 45 or requested_u > max(safe_limit_u, 0) * 1.8:
        return "HIGH"
    if predicted_max_temp >= 40 or t_cell >= 38 or requested_u >= safe_limit_u:
        return "MEDIUM"
    return "LOW"


def _build_forecast(
    soc: float,
    t_cell: float,
    predicted_max_temp: float,
    requested_u: float,
    recommended_u: float,
    direction: str,
    horizon_minutes: int,
) -> dict:
    horizon = max(horizon_minutes, 1)
    step = 5 if horizon <= 30 else 15
    minutes = list(range(0, horizon + 1, step))
    if minutes[-1] != horizon:
        minutes.append(horizon)

    soc_series = []
    temp_series = []
    requested_series = []
    recommended_series = []

    for minute in minutes:
        ratio = minute / horizon
        soc_series.append(round(_project_soc(soc, requested_u, direction, minute), 3))
        temp_series.append(round(t_cell + (predicted_max_temp - t_cell) * ratio, 1))
        requested_series.append(round(requested_u, 3))
        recommended_series.append(round(recommended_u, 3))

    return {
        "minutes": minutes,
        "soc": soc_series,
        "temperature": temp_series,
        "requested_u": requested_series,
        "recommended_u": recommended_series,
    }


def analyze_bess(data: BessInput) -> AnchorGridResult:
    anchors = load_safety_anchors()
    soc = _normalize_soc(data.soc)
    requested_u = max(float(data.u), 0)
    direction = data.direction.upper().strip()
    horizon = int(_clamp(float(data.horizon_minutes), 1, 240))

    safe_u, thermal_margin, warnings = _thermal_limit(data.t_cell, data.t_amb, data.hvac)
    safe_limit_u, blocked = _soc_limited_u(safe_u, soc, direction, warnings)
    recommended_u = min(requested_u, safe_limit_u)

    if requested_u > safe_limit_u and safe_limit_u > 0:
        warnings.append("zadany C-rate przekracza rekomendowany limit")

    soc_end = _project_soc(soc, requested_u, direction, horizon)

    predicted_max_temp = _predict_max_temp(data.t_cell, data.t_amb, requested_u, data.hvac, horizon)
    forecast_confidence_score, forecast_confidence_label = _forecast_confidence(
        horizon,
        data.t_cell,
        data.t_amb,
        requested_u,
    )
    tension = _tension(requested_u, predicted_max_temp, soc_end, forecast_confidence_score, data)

    reasons = {}
    if predicted_max_temp >= anchors.t_limit_c:
        reasons["THERMAL_LIMIT"] = _reason_detail(
            "THERMAL_LIMIT",
            f"Prognoza T_max={predicted_max_temp:.1f}°C przekracza limit {anchors.t_limit_c:.1f}°C.",
        )
    if soc_end < anchors.soc_min or soc_end > anchors.soc_max:
        reasons["SOC_BOUND"] = _reason_detail(
            "SOC_BOUND",
            f"SoC_end={soc_end:.3f} poza zakresem [{anchors.soc_min:.2f}, {anchors.soc_max:.2f}].",
        )
    if forecast_confidence_score < 0.60:
        reasons["LOW_FORECAST_CONFIDENCE"] = _reason_detail(
            "LOW_FORECAST_CONFIDENCE",
            f"forecast_confidence={forecast_confidence_score:.2f}; tryb konserwatywny.",
        )
    if tension >= anchors.tau_damped:
        reasons["TENSION_HIGH"] = _reason_detail(
            "TENSION_HIGH",
            f"tension={tension:.3f} przekracza prog DAMPED {anchors.tau_damped:.2f}.",
        )

    if blocked or safe_limit_u <= 0 or tension >= anchors.tau_locked or "THERMAL_LIMIT" in reasons:
        state = "LOCKED"
        execution_mode = "HOLD"
        decision = "Operacja niewskazana w podanych warunkach. Wymagana interwencja operatora i weryfikacja BMS/PCS."
    elif requested_u > safe_limit_u or tension >= anchors.tau_damped:
        state = "DAMPED"
        execution_mode = "CANARY"
        decision = "Operacja mozliwa tylko z redukcja C-rate i monitoringiem."
    elif thermal_margin in {"niski", "critical"}:
        state = "DAMPED"
        execution_mode = "CANARY"
        decision = "Operacja mozliwa w trybie ostroznym z monitoringiem temperatury."
    else:
        state = "STABLE"
        execution_mode = "NORMAL"
        decision = "Operacja mozliwa w zadanym zakresie advisory, przy standardowym monitoringu."

    if data.price is not None and data.price > 0:
        warnings.append("cena energii uwzgledniona informacyjnie, bez optymalizacji rynku w MVP")

    estimated_degradation_stress = _degradation_stress(
        data.t_cell,
        predicted_max_temp,
        requested_u,
        safe_limit_u,
    )
    economics = _economics(requested_u, predicted_max_temp, soc_end, horizon, data.price)
    if economics["net_value_pln"] < 0 and data.price is not None:
        reasons["NET_VALUE_NEGATIVE"] = _reason_detail(
            "NET_VALUE_NEGATIVE",
            f"Net value {economics['net_value_pln']:.0f} PLN; operacja moze niszczyc wartosc.",
        )
    forecast = _build_forecast(
        soc,
        data.t_cell,
        predicted_max_temp,
        requested_u,
        recommended_u,
        direction,
        horizon,
    )

    return AnchorGridResult(
        product="BESS Safety & Dispatch Advisory Engine",
        advisory_only=True,
        state=state,
        execution_mode=execution_mode,
        operation=direction,
        requested_u=f"{requested_u:.2g}C",
        recommended_u_safe=_format_c_rate(recommended_u),
        recommended_u_safe_value=recommended_u,
        thermal_margin=thermal_margin,
        predicted_max_temp=predicted_max_temp,
        forecast_confidence=f"{forecast_confidence_score:.2f} ({forecast_confidence_label})",
        forecast_confidence_score=forecast_confidence_score,
        forecast_confidence_label=forecast_confidence_label,
        estimated_degradation_stress=estimated_degradation_stress,
        tension=tension,
        reasons=reasons,
        economics=economics,
        source_legacy_assets=[
            str(LEGACY_SAFETY_ANCHORS),
            str(LEGACY_BATTERY_ECONOMICS),
            str(LEGACY_REASON_REGISTRY),
        ],
        soc_projection_15m=f"{soc:.2f} -> {soc_end:.2f}",
        soc_start=round(soc, 3),
        soc_end=round(soc_end, 3),
        forecast=forecast,
        warnings=warnings,
        decision=decision,
        disclaimer=(
            "Symulacja operacyjna / advisory / decision-support dla BESS. "
            "To nie jest prawdziwa decyzja bezpieczenstwa BMS. Finalne decyzje "
            "naleza do BMS/PCS/operatora."
        ),
    )
