from app.anchorgrid.engine import analyze_bess
from app.anchorgrid.schemas import BessInput


def test_recommendation_never_exceeds_requested_c_rate() -> None:
    result = analyze_bess(
        BessInput(
            soc=50,
            t_cell=25,
            t_amb=20,
            u=0.4,
            hvac=True,
            direction="DISCHARGE",
            horizon_minutes=15,
        )
    )

    assert result.requested_u == "0.4C"
    assert result.recommended_u_safe == "okolo 0.4C"
    assert result.recommended_u_safe_value == 0.4
    assert result.state == "STABLE"
    assert result.estimated_degradation_stress == "LOW"
    assert result.forecast_confidence == "0.85 (HIGH)"
    assert result.forecast_confidence_score == 0.85
    assert result.forecast_confidence_label == "HIGH"
    assert result.predicted_max_temp >= 25
    assert result.forecast["minutes"][-1] == 15


def test_recommendation_caps_requested_c_rate_when_limit_is_lower() -> None:
    result = analyze_bess(
        BessInput(
            soc=78,
            t_cell=39,
            t_amb=31,
            u=0.8,
            hvac=True,
            direction="DISCHARGE",
            horizon_minutes=15,
        )
    )

    assert result.requested_u == "0.8C"
    assert result.recommended_u_safe == "okolo 0.5C"
    assert result.recommended_u_safe_value == 0.5
    assert result.state == "LOCKED"
    assert result.execution_mode == "HOLD"
    assert result.estimated_degradation_stress == "MEDIUM"
    assert "THERMAL_LIMIT" in result.reasons


def test_low_soc_discharge_locks_operation() -> None:
    result = analyze_bess(
        BessInput(
            soc=5,
            t_cell=25,
            t_amb=20,
            u=0.2,
            hvac=True,
            direction="DISCHARGE",
            horizon_minutes=15,
        )
    )

    assert result.state == "LOCKED"
    assert result.execution_mode == "HOLD"
    assert result.recommended_u_safe_value == 0
