from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MetricPayload:
    epoch: int
    total_epochs: int
    loss: float
    duration_sec: float
    device: str
    tags: list[str]
    anomaly_score: float = 0.0
    normalized_score: float = 0.0
    safe_state: str = "PASSIVE"
    drift_dimensions: dict[str, float] = field(default_factory=dict)
    is_stable: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "epoch": self.epoch,
            "total_epochs": self.total_epochs,
            "loss": self.loss,
            "duration_sec": self.duration_sec,
            "device": self.device,
            "tags": self.tags,
            "anomaly_score": self.anomaly_score,
            "normalized_score": self.normalized_score,
            "safe_state": self.safe_state,
            "drift_dimensions": self.drift_dimensions,
            "is_stable": self.is_stable,
        }


@dataclass(frozen=True)
class TraceEvent:
    timestamp: float
    metric_type: str
    raw_value: float
    historical_avg: float
    drift_score: float
    normalized_score: float
    threshold: float
    stable: bool
    safe_state: str
    classification: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "metric_type": self.metric_type,
            "raw_value": self.raw_value,
            "historical_avg": self.historical_avg,
            "drift_score": self.drift_score,
            "normalized_score": self.normalized_score,
            "threshold": self.threshold,
            "stable": self.stable,
            "safe_state": self.safe_state,
            "classification": self.classification,
        }


class SafeEngine:
    def evaluate(self, score: float, threshold: float) -> str:
        if score > threshold * 4:
            return "STOP"
        if score > threshold * 3:
            return "LOCK"
        if score > threshold * 2:
            return "CONTAIN"
        if score > threshold:
            return "ALIGN"
        return "PASSIVE"


class DriftEngine:
    def __init__(self, threshold: float = 0.5, window_size: int = 5, epsilon: float = 1e-8) -> None:
        self.threshold = threshold
        self.window_size = window_size
        self.epsilon = epsilon
        self.history: list[float] = []
        self.trace_history: list[TraceEvent] = []
        self.safe_history: list[str] = []
        self.safe_engine = SafeEngine()

    def detect_trend(self) -> str:
        if len(self.history) < self.window_size:
            return "INSUFFICIENT_DATA"
        y = self.history[-self.window_size :]
        x_mean = (len(y) - 1) / 2
        y_mean = sum(y) / len(y)
        numerator = sum((index - x_mean) * (value - y_mean) for index, value in enumerate(y))
        denominator = sum((index - x_mean) ** 2 for index in range(len(y))) or self.epsilon
        slope = numerator / denominator
        if slope > 0.1:
            return "PROGRESSIVE_DRIFT"
        if slope < -0.1:
            return "RECOVERY"
        return "STABLE"

    def check(self, current_loss: float) -> tuple[MetricPayload, TraceEvent]:
        if len(self.history) < self.window_size:
            self.history.append(current_loss)
            payload = MetricPayload(
                epoch=0,
                total_epochs=0,
                loss=current_loss,
                duration_sec=0.0,
                device="bootstrap",
                tags=["bootstrap"],
                drift_dimensions={"D_loss": 0.0, "D_trend": 0.0, "D_context": 0.0},
                is_stable=True,
            )
            trace = TraceEvent(
                timestamp=time.time(),
                metric_type="knowledge_risk",
                raw_value=current_loss,
                historical_avg=current_loss,
                drift_score=0.0,
                normalized_score=0.0,
                threshold=self.threshold,
                stable=True,
                safe_state="PASSIVE",
                classification="BOOTSTRAP",
            )
            return payload, trace

        historical_window = self.history[-self.window_size :]
        recent_avg = sum(historical_window) / len(historical_window)
        raw_score = abs(current_loss - recent_avg)
        normalized_score = raw_score / (abs(recent_avg) + self.epsilon)
        trend = self.detect_trend()
        safe_state = self.safe_engine.evaluate(normalized_score, self.threshold)
        stable = safe_state == "PASSIVE"
        if normalized_score > self.threshold * 3:
            classification = "COLLAPSE_DRIFT"
        elif normalized_score > self.threshold:
            classification = "SPIKE_DRIFT"
        elif trend == "PROGRESSIVE_DRIFT":
            classification = "PROGRESSIVE_DRIFT"
        else:
            classification = "NORMAL"
        self.history.append(current_loss)
        self.safe_history.append(safe_state)
        payload = MetricPayload(
            epoch=0,
            total_epochs=0,
            loss=round(current_loss, 6),
            duration_sec=0.0,
            device="local",
            tags=["knowledge_os", "risk_mapping"],
            anomaly_score=round(raw_score, 6),
            normalized_score=round(normalized_score, 6),
            safe_state=safe_state,
            drift_dimensions={
                "D_loss": round(normalized_score, 4),
                "D_trend": 1.0 if trend == "PROGRESSIVE_DRIFT" else 0.0,
                "D_context": 0.0,
            },
            is_stable=stable,
        )
        trace = TraceEvent(
            timestamp=time.time(),
            metric_type="knowledge_risk",
            raw_value=current_loss,
            historical_avg=recent_avg,
            drift_score=raw_score,
            normalized_score=normalized_score,
            threshold=self.threshold,
            stable=stable,
            safe_state=safe_state,
            classification=classification,
        )
        self.trace_history.append(trace)
        return payload, trace


def build_risk_map(report_context: dict[str, Any]) -> dict[str, Any]:
    chunks = report_context.get("chunks", [])
    blocked = report_context.get("blocked_recommendation_claims", [])
    evidence = report_context.get("evidence_map", [])
    total = max(len(chunks), 1)
    review_ratio = len(blocked) / total
    low_confidence = [
        item for item in evidence
        if isinstance(item.get("confidence"), (int, float)) and item["confidence"] < 0.6
    ]
    loss = min(1.0, review_ratio + (len(low_confidence) / total * 0.5))
    safe_engine = SafeEngine()
    safe_state = safe_engine.evaluate(loss, 0.25)
    classification = "NORMAL"
    if safe_state == "STOP":
        classification = "KNOWLEDGE_OUTPUT_BLOCKED"
    elif safe_state in {"LOCK", "CONTAIN"}:
        classification = "HUMAN_REVIEW_REQUIRED"
    elif safe_state == "ALIGN":
        classification = "VALIDATION_ALIGNMENT_REQUIRED"
    payload = MetricPayload(
        epoch=0,
        total_epochs=0,
        loss=round(loss, 6),
        duration_sec=0.0,
        device="local",
        tags=["knowledge_os", "risk_mapping"],
        anomaly_score=round(loss, 6),
        normalized_score=round(loss, 6),
        safe_state=safe_state,
        drift_dimensions={
            "D_loss": round(loss, 4),
            "D_trend": 0.0,
            "D_context": round(review_ratio, 4),
        },
        is_stable=safe_state == "PASSIVE",
    )
    trace = TraceEvent(
        timestamp=time.time(),
        metric_type="knowledge_risk",
        raw_value=loss,
        historical_avg=0.0,
        drift_score=loss,
        normalized_score=loss,
        threshold=0.25,
        stable=safe_state == "PASSIVE",
        safe_state=safe_state,
        classification=classification,
    )
    return {
        "risk_score": round(loss, 4),
        "review_ratio": round(review_ratio, 4),
        "blocked_count": len(blocked),
        "low_confidence_count": len(low_confidence),
        "safe_state": payload.safe_state,
        "classification": trace.classification,
        "metric_payload": payload.as_dict(),
        "trace_event": trace.as_dict(),
    }
