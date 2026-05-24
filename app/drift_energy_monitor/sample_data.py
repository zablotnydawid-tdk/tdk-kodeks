from __future__ import annotations

from .schemas import (
    AiLayerSnapshot,
    EconomicsSnapshot,
    EnvironmentalSnapshot,
    MonitorSnapshot,
    RuntimeSnapshot,
    TelemetrySnapshot,
)


def stable_snapshot() -> MonitorSnapshot:
    return MonitorSnapshot(
        telemetry=TelemetrySnapshot(
            inverter_power=42.0,
            grid_import=0.0,
            grid_export=8.0,
            battery_soc=72.0,
            phase_balance={"l1": 31.0, "l2": 30.0, "l3": 32.0},
            voltage=231.0,
            current=18.0,
            temperature=38.0,
        ),
        runtime=RuntimeSnapshot(total_events=100, unexpected_events=4),
        ai_layer=AiLayerSnapshot(
            stable_decisions=96,
            total_decisions=100,
            contradiction_events=2,
            total_predictions=100,
            confidence_score=0.92,
        ),
        economics=EconomicsSnapshot(
            tariff_window="standard",
            expected_cost=500.0,
            actual_cost=470.0,
            expected_yield=100.0,
            real_yield=96.0,
            optimization_delta_pln=45.0,
        ),
        environmental=EnvironmentalSnapshot(
            weather="clear",
            irradiance=720.0,
            humidity=48.0,
            ambient_temperature=21.0,
        ),
    )


def drift_snapshot() -> MonitorSnapshot:
    return MonitorSnapshot(
        telemetry=TelemetrySnapshot(
            inverter_power=37.0,
            grid_import=11.0,
            grid_export=14.0,
            battery_soc=63.0,
            phase_balance={"l1": 18.0, "l2": 53.0, "l3": 22.0},
            voltage=226.0,
            current=41.0,
            temperature=51.0,
        ),
        runtime=RuntimeSnapshot(
            event_latency=1.4,
            queue_depth=17,
            api_response_time=2.3,
            retry_cycles=6,
            watchdog_alerts=2,
            unexpected_events=41,
            total_events=100,
        ),
        ai_layer=AiLayerSnapshot(
            stable_decisions=52,
            total_decisions=100,
            contradiction_events=31,
            total_predictions=100,
            repeated_decisions=7,
            no_state_change=True,
            confidence_score=0.48,
        ),
        economics=EconomicsSnapshot(
            tariff_window="peak",
            energy_price=1.31,
            import_cost=730.0,
            export_value=80.0,
            expected_cost=510.0,
            actual_cost=860.0,
            expected_yield=110.0,
            real_yield=83.0,
            optimization_delta_pln=-165.0,
        ),
        environmental=EnvironmentalSnapshot(
            weather="stable_cloud",
            irradiance=540.0,
            humidity=66.0,
            ambient_temperature=19.5,
            outside_temp_stable=True,
            cop_drop=24.0,
        ),
    )


def recovery_snapshot() -> MonitorSnapshot:
    return MonitorSnapshot(
        telemetry=TelemetrySnapshot(
            inverter_power=44.0,
            grid_import=0.0,
            grid_export=6.0,
            battery_soc=76.0,
            phase_balance={"l1": 32.0, "l2": 31.0, "l3": 33.0},
            voltage=230.0,
            current=18.5,
            temperature=39.0,
        ),
        runtime=RuntimeSnapshot(
            unexpected_events=2,
            total_events=100,
            recovery_successful=True,
        ),
        ai_layer=AiLayerSnapshot(
            stable_decisions=97,
            total_decisions=100,
            contradiction_events=1,
            total_predictions=100,
            confidence_score=0.95,
        ),
        economics=EconomicsSnapshot(
            tariff_window="standard",
            expected_cost=500.0,
            actual_cost=472.0,
            expected_yield=100.0,
            real_yield=98.0,
            optimization_delta_pln=52.0,
        ),
        environmental=EnvironmentalSnapshot(
            weather="clear",
            irradiance=735.0,
            humidity=46.0,
            ambient_temperature=21.0,
        ),
    )


def sample_snapshots() -> list[MonitorSnapshot]:
    return [stable_snapshot(), drift_snapshot(), recovery_snapshot()]
