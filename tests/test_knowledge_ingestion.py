from __future__ import annotations

from pathlib import Path

from knowledge.document_ingestor import ingest_document
from knowledge.domain_classifier import KNOWLEDGE_DOMAINS, classify_domain
from knowledge.drift_energy import AnomalyDetector, TraceEvent, TrainingMetricPayload, build_training_metric_payload
from knowledge.ingestion_engine import run_knowledge_os


def test_domain_classifier_recognizes_required_domains() -> None:
    assert "REGULATORY" in KNOWLEDGE_DOMAINS
    assert "TECHNICAL" in KNOWLEDGE_DOMAINS
    assert "FIELD_PROCEDURE" in KNOWLEDGE_DOMAINS
    assert "FINANCIAL" in KNOWLEDGE_DOMAINS
    assert "SUBSIDY" in KNOWLEDGE_DOMAINS
    assert "BILLING" in KNOWLEDGE_DOMAINS
    assert "VPP_ALGORITHM" in KNOWLEDGE_DOMAINS
    assert "CLIENT_EVIDENCE" in KNOWLEDGE_DOMAINS

    assert classify_domain("Ustawa i rozporzadzenie wymagaja audytu regulacyjnego").domain == "REGULATORY"
    assert classify_domain("CSIRE i net-billing wymagaja walidacji rozliczenia").domain == "BILLING"
    assert classify_domain("Falownik pokazuje 253V i wymaga diagnostyki pomiarowej").domain == "TECHNICAL"
    assert classify_domain("Dotacja OZE 2026 wymaga sprawdzenia warunkow programu").domain == "SUBSIDY"
    assert classify_domain("VPP dispatch steruje BESS w oknie taryfowym").domain == "VPP_ALGORITHM"


def test_ingestion_builds_trace_and_blocks_unvalidated_complex_claims(tmp_path: Path) -> None:
    source = tmp_path / "complex_case.md"
    source.write_text(
        "\n".join(
            [
                "Dotacja OZE 2026 wymaga sprawdzenia warunkow programu przed rekomendacja.",
                "Falownik pokazuje 253V, wiec procedura polowa wymaga pomiaru napiecia.",
                "Faktura klienta wskazuje strate 360 PLN w rozliczeniu net-billing.",
            ]
        ),
        encoding="utf-8",
    )

    result = ingest_document(source, max_chars=120)
    context = result.report_context.as_dict()

    assert result.chunks
    assert context["ready_for_client_recommendation"] is False
    assert context["blocked_recommendation_claims"]
    assert context["source_graph"]["nodes"]
    assert context["source_graph"]["risk_map"]
    assert context["source_graph"]["dependency_map"]

    traces = [chunk.trace.as_dict() for chunk in result.chunks]
    for trace in traces:
        assert trace["source_file"] == str(source)
        assert "domain" in trace
        assert "claim" in trace
        assert "evidence_type" in trace
        assert "confidence" in trace
        assert "requires_human_review" in trace


def test_simple_client_evidence_can_be_report_ready_when_trace_is_valid(tmp_path: Path) -> None:
    source = tmp_path / "client_measurement.txt"
    source.write_text("Klient przekazal csv z pomiarem produkcji PV oraz faktura.", encoding="utf-8")

    result = ingest_document(source)
    context = result.report_context.as_dict()

    assert context["chunks"]
    assert context["evidence_map"][0]["source_file"] == str(source)
    assert context["evidence_map"][0]["validation_status"] == "TRACE_VALID"


def test_knowledge_os_builds_decision_map_and_human_review_queue(tmp_path: Path) -> None:
    source = tmp_path / "regulatory_case.md"
    source.write_text("Net-billing i CSIRE wymagaja walidacji operatora przed raportem klienta.", encoding="utf-8")

    result = run_knowledge_os(source)
    payload = result.as_dict()

    assert payload["decision_map"]["decision"] == "HUMAN_VALIDATION_REQUIRED"
    assert payload["decision_map"]["validation_level"] == "human_required"
    assert payload["drift_energy"]["payload"]["safe_state"] in {"CONTAIN", "LOCK"}
    assert payload["drift_energy"]["trace"]["classification"] in {"CONTAINMENT_DRIFT", "COLLAPSE_DRIFT"}
    assert payload["human_review_queue"]
    assert "No recommendation without trace" in payload["operator_report_markdown"]


def test_drift_energy_detector_moves_to_align_on_loss_spike() -> None:
    detector = AnomalyDetector(threshold=0.5, window_size=3)
    for loss in (0.9, 0.88, 0.86):
        _, _, _, _, trace = detector.check(loss)
        assert isinstance(trace, TraceEvent)

    payload = build_training_metric_payload(
        detector=detector,
        epoch=3,
        total_epochs=10,
        total_epoch_loss=1.6,
        epoch_duration=1.23,
        device="cuda",
    )

    assert payload.epoch == 4
    assert payload.safe_state in {"ALIGN", "CONTAIN", "LOCK"}
    assert payload.is_stable is False
    assert payload.normalized_score > 0


def test_drift_energy_regression_align_for_known_loss_window() -> None:
    detector = AnomalyDetector(threshold=0.5, window_size=3)
    for loss in (0.91, 0.88, 0.86):
        detector.check(loss)

    payload = build_training_metric_payload(
        detector=detector,
        epoch=3,
        total_epochs=10,
        total_epoch_loss=1.60,
        epoch_duration=1.23,
        device="cuda",
    )

    assert payload.is_stable is False
    assert payload.safe_state == "ALIGN"
    assert abs(payload.normalized_score - 0.8113) < 0.0001


def test_drift_energy_detector_returns_trace_and_exports_json() -> None:
    detector = AnomalyDetector(threshold=0.5, window_size=3)
    for loss in (1.0, 1.0, 1.0):
        detector.check(loss)

    score, normalized_score, stable, safe_state, trace = detector.check(1.1)
    payload = TrainingMetricPayload(
        epoch=1,
        total_epochs=1,
        loss=1.1,
        duration_sec=0.1,
        device="local",
        tags=["test"],
        anomaly_score=score,
        normalized_score=normalized_score,
        safe_state=safe_state,
        is_stable=stable,
    )

    assert safe_state == "PASSIVE"
    assert trace.classification == "NORMAL"
    assert '"safe_state": "PASSIVE"' in payload.to_json()
    assert '"classification": "NORMAL"' in trace.to_json()


def test_drift_energy_detector_moves_to_contain() -> None:
    detector = AnomalyDetector(threshold=0.5, window_size=3)
    for loss in (1.0, 1.0, 1.0):
        detector.check(loss)

    score, normalized_score, stable, safe_state, trace = detector.check(2.1)

    assert round(score, 4) == 1.1
    assert normalized_score >= detector.threshold * 2
    assert normalized_score < detector.threshold * 3
    assert stable is False
    assert safe_state == "CONTAIN"
    assert trace.safe_state == "CONTAIN"
    assert trace.classification == "CONTAINMENT_DRIFT"


def test_drift_energy_detector_moves_to_lock() -> None:
    detector = AnomalyDetector(threshold=0.5, window_size=3)
    for loss in (1.0, 1.0, 1.0):
        detector.check(loss)

    score, normalized_score, stable, safe_state, trace = detector.check(2.6)

    assert round(score, 4) == 1.6
    assert normalized_score >= detector.threshold * 3
    assert stable is False
    assert safe_state == "LOCK"
    assert trace.safe_state == "LOCK"
    assert trace.classification == "COLLAPSE_DRIFT"
