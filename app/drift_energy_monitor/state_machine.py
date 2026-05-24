from __future__ import annotations

from .schemas import MonitorSnapshot, MonitorState


class DriftEnergyStateMachine:
    def transition(
        self,
        current_state: MonitorState,
        metrics: dict[str, float],
        snapshot: MonitorSnapshot,
        metrics_normalized: bool,
    ) -> MonitorState:
        if current_state == MonitorState.STABLE and metrics["runtime_entropy"] > 0.15:
            return MonitorState.OBSERVATION
        if (
            current_state == MonitorState.OBSERVATION
            and metrics["coherence_index"] < 85.0
        ):
            return MonitorState.DEGRADED
        if (
            current_state == MonitorState.DEGRADED
            and metrics["energy_loss_factor"] > 20.0
        ):
            return MonitorState.UNSTABLE
        if (
            current_state == MonitorState.UNSTABLE
            and metrics["ai_conflict_ratio"] > 0.25
        ):
            return MonitorState.CRITICAL
        if (
            current_state == MonitorState.CRITICAL
            and snapshot.runtime.subsystem_failure_detected
        ):
            return MonitorState.ISOLATED
        if (
            current_state == MonitorState.CRITICAL
            and snapshot.runtime.recovery_successful
            and metrics_normalized
        ):
            return MonitorState.RECOVERY
        if (
            current_state == MonitorState.ISOLATED
            and snapshot.runtime.recovery_successful
        ):
            return MonitorState.RECOVERY
        if current_state == MonitorState.RECOVERY and metrics_normalized:
            return MonitorState.STABLE
        return current_state

    def state_for_metrics(
        self, metrics: dict[str, float], snapshot: MonitorSnapshot
    ) -> MonitorState:
        if snapshot.runtime.subsystem_failure_detected:
            return MonitorState.ISOLATED
        if metrics["ai_conflict_ratio"] > 0.25:
            return MonitorState.CRITICAL
        if metrics["energy_loss_factor"] > 20.0:
            return MonitorState.UNSTABLE
        if metrics["coherence_index"] < 85.0:
            return MonitorState.DEGRADED
        if metrics["runtime_entropy"] > 0.15:
            return MonitorState.OBSERVATION
        return MonitorState.STABLE


def metrics_normalized(metrics: dict[str, float]) -> bool:
    return (
        metrics["coherence_index"] >= 85.0
        and metrics["runtime_entropy"] <= 0.15
        and metrics["energy_loss_factor"] <= 8.0
        and metrics["economic_drift"] <= 50.0
        and metrics["ai_conflict_ratio"] <= 0.10
    )
