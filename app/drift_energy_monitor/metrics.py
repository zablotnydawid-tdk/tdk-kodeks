from __future__ import annotations

from .schemas import MonitorSnapshot, Severity


class DriftMetricsEngine:
    def calculate(self, snapshot: MonitorSnapshot) -> dict[str, float]:
        ai = snapshot.ai_layer
        runtime = snapshot.runtime
        economics = snapshot.economics
        coherence_index = self._percent(ai.stable_decisions, ai.total_decisions)
        runtime_entropy = self._ratio(runtime.unexpected_events, runtime.total_events)
        energy_loss_factor = economics.expected_yield - economics.real_yield
        economic_drift = economics.actual_cost - economics.expected_cost
        ai_conflict_ratio = self._ratio(
            ai.contradiction_events, ai.total_predictions
        )
        return {
            "coherence_index": round(coherence_index, 4),
            "runtime_entropy": round(runtime_entropy, 4),
            "energy_loss_factor": round(energy_loss_factor, 4),
            "economic_drift": round(economic_drift, 4),
            "ai_conflict_ratio": round(ai_conflict_ratio, 4),
        }

    def classify(self, metrics: dict[str, float]) -> dict[str, Severity]:
        return {
            "coherence_index": self._low_is_bad(
                metrics["coherence_index"], warning=85.0, critical=60.0
            ),
            "runtime_entropy": self._high_is_bad(
                metrics["runtime_entropy"], warning=0.15, critical=0.35
            ),
            "energy_loss_factor": self._high_is_bad(
                metrics["energy_loss_factor"], warning=8.0, critical=20.0
            ),
            "economic_drift": self._high_is_bad(
                metrics["economic_drift"], warning=50.0, critical=300.0
            ),
            "ai_conflict_ratio": self._high_is_bad(
                metrics["ai_conflict_ratio"], warning=0.10, critical=0.25
            ),
        }

    def _ratio(self, numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    def _percent(self, numerator: float, denominator: float) -> float:
        return self._ratio(numerator, denominator) * 100.0

    def _high_is_bad(self, value: float, warning: float, critical: float) -> Severity:
        if value > critical:
            return Severity.CRITICAL
        if value > warning:
            return Severity.WARNING
        return Severity.INFO

    def _low_is_bad(self, value: float, warning: float, critical: float) -> Severity:
        if value < critical:
            return Severity.CRITICAL
        if value < warning:
            return Severity.WARNING
        return Severity.INFO
