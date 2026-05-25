from __future__ import annotations

import logging
import json
import time
from dataclasses import asdict, dataclass
from typing import Any


logger = logging.getLogger("EXIM-DriftEnergy")


@dataclass(frozen=True)
class TrainingMetricPayload:
    epoch: int
    total_epochs: int
    loss: float
    duration_sec: float
    device: str
    tags: list[str]
    anomaly_score: float = 0.0
    normalized_score: float = 0.0
    safe_state: str = "PASSIVE"
    is_stable: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True)


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
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True)


class AnomalyDetector:
    def __init__(self, threshold: float = 0.5, window_size: int = 3, epsilon: float = 1e-8) -> None:
        self.threshold = threshold
        self.window_size = window_size
        self.epsilon = epsilon
        self.history: list[float] = []

    def check(self, current_loss: float) -> tuple[float, float, bool, str, TraceEvent]:
        if len(self.history) < self.window_size:
            self.history.append(current_loss)
            trace = TraceEvent(
                timestamp=time.time(),
                metric_type="loss",
                raw_value=current_loss,
                historical_avg=current_loss,
                drift_score=0.0,
                normalized_score=0.0,
                threshold=self.threshold,
                stable=True,
                safe_state="PASSIVE",
                classification="BOOTSTRAP",
            )
            return 0.0, 0.0, True, "PASSIVE", trace

        historical_window = self.history[-self.window_size :]
        recent_avg = sum(historical_window) / len(historical_window)
        raw_score = abs(current_loss - recent_avg)
        normalized_score = raw_score / (abs(recent_avg) + self.epsilon)
        self.history.append(current_loss)

        if normalized_score >= self.threshold * 3:
            safe_state = "LOCK"
        elif normalized_score >= self.threshold * 2:
            safe_state = "CONTAIN"
        elif normalized_score >= self.threshold:
            safe_state = "ALIGN"
        else:
            safe_state = "PASSIVE"

        stable = safe_state == "PASSIVE"
        if safe_state == "LOCK":
            classification = "COLLAPSE_DRIFT"
        elif safe_state == "CONTAIN":
            classification = "CONTAINMENT_DRIFT"
        elif safe_state == "ALIGN":
            classification = "SPIKE_DRIFT"
        else:
            classification = "NORMAL"

        trace = TraceEvent(
            timestamp=time.time(),
            metric_type="loss",
            raw_value=current_loss,
            historical_avg=recent_avg,
            drift_score=float(raw_score),
            normalized_score=float(normalized_score),
            threshold=self.threshold,
            stable=stable,
            safe_state=safe_state,
            classification=classification,
        )
        return float(raw_score), float(normalized_score), stable, safe_state, trace


def build_training_metric_payload(
    detector: AnomalyDetector,
    epoch: int,
    total_epochs: int,
    total_epoch_loss: float,
    epoch_duration: float,
    device: str,
    tags: list[str] | None = None,
) -> TrainingMetricPayload:
    score, normalized_score, stable, safe_state, trace = detector.check(total_epoch_loss)
    payload = TrainingMetricPayload(
        epoch=epoch + 1,
        total_epochs=total_epochs,
        loss=round(total_epoch_loss, 4),
        duration_sec=round(epoch_duration, 2),
        device=str(device),
        tags=tags or ["train", "binary_classification", "exim_runtime"],
        anomaly_score=round(score, 4),
        normalized_score=round(normalized_score, 4),
        safe_state=safe_state,
        is_stable=stable,
    )
    if not stable:
        logger.warning(
            "[EXIM SAFE:%s] Drift Energy detected at epoch %s",
            safe_state,
            epoch + 1,
            extra={"metrics": payload.as_dict(), "trace": trace.as_dict()},
        )
    else:
        logger.info(
            "[EXIM STABLE] Epoch %s/%s completed",
            epoch + 1,
            total_epochs,
            extra={"metrics": payload.as_dict(), "trace": trace.as_dict()},
        )
    return payload


def build_document_drift_energy(
    risk_score: float,
    threshold: float = 0.5,
    baseline: float = 0.25,
) -> dict[str, Any]:
    detector = AnomalyDetector(threshold=threshold, window_size=3)
    detector.history = [baseline, baseline, baseline]
    score, normalized_score, stable, safe_state, trace = detector.check(risk_score)
    payload = TrainingMetricPayload(
        epoch=1,
        total_epochs=1,
        loss=round(risk_score, 4),
        duration_sec=0.0,
        device="local",
        tags=["knowledge_os", "document_risk", "exim_runtime"],
        anomaly_score=round(score, 4),
        normalized_score=round(normalized_score, 4),
        safe_state=safe_state,
        is_stable=stable,
    )
    return {
        "payload": payload.as_dict(),
        "trace": trace.as_dict(),
    }
