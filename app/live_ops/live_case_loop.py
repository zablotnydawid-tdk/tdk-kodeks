from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRIORITY_ORDER = {"low": 1, "normal": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class LiveCaseMemoryEntry:
    step: str
    summary: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiveCaseResult:
    case_id: str
    generated_at: str
    intake: dict[str, Any]
    classification: dict[str, Any]
    priority: dict[str, Any]
    diagnostic_summary: dict[str, Any]
    recommendation: dict[str, Any]
    memory: dict[str, Any]
    executive_summary: str
    governance: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def intake(payload: dict[str, Any]) -> dict[str, Any]:
    text = _join_text(
        [
            payload.get("title", ""),
            payload.get("description", ""),
            payload.get("customer_context", ""),
        ]
    )
    signals = _extract_signals(payload, text)
    return {
        "case_id": payload.get("case_id") or "live-case-local",
        "received_at": payload.get("received_at") or _now(),
        "source": payload.get("source", "manual_operator_input"),
        "operator_id": payload.get("operator_id", "local-operator"),
        "title": payload.get("title", "Untitled live case"),
        "description": payload.get("description", ""),
        "customer_context": payload.get("customer_context", ""),
        "assets": list(payload.get("assets", [])),
        "measurements": dict(payload.get("measurements", {})),
        "reported_symptoms": list(payload.get("reported_symptoms", [])),
        "requested_outcome": payload.get("requested_outcome", "diagnostic summary"),
        "raw_text": text,
        "signals": signals,
    }


def classify_case(intake_record: dict[str, Any]) -> dict[str, Any]:
    text = intake_record["raw_text"].lower()
    symptoms = " ".join(intake_record.get("reported_symptoms", [])).lower()
    combined = f"{text} {symptoms}"
    categories: list[str] = []

    if _contains_any(combined, ("pv", "fotowolta", "falownik", "inverter")):
        categories.append("pv")
    if _contains_any(combined, ("ems", "bms", "battery", "bess", "magazyn")):
        categories.append("ems_bess")
    if _contains_any(combined, ("pompa", "heat pump", "cop", "temperatura")):
        categories.append("heat_pump")
    if _contains_any(
        combined,
        ("koszt", "rachunek", "taryfa", "pln", "energia", "cost", "bill", "tariff"),
    ):
        categories.append("economics")
    if _contains_any(combined, ("ai", "decyzja", "sprzeczn", "loop", "governance")):
        categories.append("ai_governance")
    if _contains_any(combined, ("faza", "phase", "napiecie", "voltage", "prad")):
        categories.append("electrical_safety")

    if not categories:
        categories.append("general_energy_ops")

    return {
        "primary_type": categories[0],
        "categories": categories,
        "case_domain": "live_energy_operations",
        "confidence": _classification_confidence(categories, intake_record),
        "operator_decision_required": True,
    }


def detect_priority(
    intake_record: dict[str, Any], classification: dict[str, Any]
) -> dict[str, Any]:
    signals = intake_record.get("signals", {})
    measurements = intake_record.get("measurements", {})
    reasons: list[str] = []
    priority = "normal"

    if classification["primary_type"] == "electrical_safety":
        priority = _max_priority(priority, "high")
        reasons.append("electrical safety category detected")

    if signals.get("critical_language"):
        priority = _max_priority(priority, "high")
        reasons.append("critical language detected")

    if measurements.get("phase_imbalance_percent", 0) >= 25:
        priority = _max_priority(priority, "critical")
        reasons.append("phase imbalance above critical local threshold")

    if measurements.get("economic_loss_pln", 0) >= 300:
        priority = _max_priority(priority, "high")
        reasons.append("reported economic loss exceeds high threshold")

    if measurements.get("runtime_entropy", 0) >= 0.35:
        priority = _max_priority(priority, "critical")
        reasons.append("runtime entropy exceeds critical threshold")

    if not reasons:
        reasons.append("no immediate critical signal detected")

    return {
        "level": priority,
        "reasons": reasons,
        "operator_override_supported": True,
        "autonomous_action_allowed": False,
    }


def generate_diagnostic_summary(
    intake_record: dict[str, Any],
    classification: dict[str, Any],
    priority: dict[str, Any],
) -> dict[str, Any]:
    measurements = intake_record.get("measurements", {})
    findings: list[str] = []

    if "pv" in classification["categories"]:
        findings.append("PV / inverter context is present and should be checked against yield and EMS behavior.")
    if "ems_bess" in classification["categories"]:
        findings.append("EMS/BESS context is present; verify charge source, SoC policy, and operator limits.")
    if "heat_pump" in classification["categories"]:
        findings.append("Heat pump context is present; compare COP, flow temperature, and ambient conditions.")
    if "economics" in classification["categories"]:
        loss = measurements.get("economic_loss_pln")
        if loss is not None:
            findings.append(f"Economic loss signal reported at {loss} PLN.")
        else:
            findings.append("Economic context is present; collect tariff and consumption evidence.")
    if "ai_governance" in classification["categories"]:
        findings.append("AI governance context is present; require trace review before accepting recommendations.")
    if "electrical_safety" in classification["categories"]:
        findings.append("Electrical safety context is present; keep recommendations operator-gated.")

    if not findings:
        findings.append("Case requires baseline operator review and more measurements.")

    evidence_gaps = _evidence_gaps(intake_record, classification)

    return {
        "summary": f"{classification['primary_type']} case with {priority['level']} priority.",
        "findings": findings,
        "evidence_gaps": evidence_gaps,
        "traceability": "all findings derived from local input only",
    }


def generate_recommendation(
    intake_record: dict[str, Any],
    classification: dict[str, Any],
    priority: dict[str, Any],
    diagnostic_summary: dict[str, Any],
) -> dict[str, Any]:
    actions = ["operator reviews intake and diagnostic summary"]

    if priority["level"] in ("high", "critical"):
        actions.append("hold any field action until operator confirms risk boundary")
    if "pv" in classification["categories"]:
        actions.append("collect inverter yield, grid import/export, and EMS charge logs")
    if "ems_bess" in classification["categories"]:
        actions.append("check BMS/PCS limits, SoC policy, and charge/discharge intent")
    if "heat_pump" in classification["categories"]:
        actions.append("collect flow temperature, outside temperature, and COP trend")
    if "economics" in classification["categories"]:
        actions.append("attach tariff, invoice, and expected vs actual cost comparison")
    if "ai_governance" in classification["categories"]:
        actions.append("preserve decision trace and require manual acceptance")
    if diagnostic_summary["evidence_gaps"]:
        actions.append("fill evidence gaps before customer-facing conclusion")

    return {
        "operator_next_actions": actions,
        "customer_safe_message": _customer_safe_message(priority["level"]),
        "blocked_actions": [
            "no autonomous remediation",
            "no EMS/PV/BESS command execution",
            "no cloud sync",
            "no frontend/backend integration in this proof",
        ],
        "decision_owner": "operator",
    }


def memory_update(
    intake_record: dict[str, Any],
    classification: dict[str, Any],
    priority: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    recommendation: dict[str, Any],
) -> dict[str, Any]:
    entries = [
        LiveCaseMemoryEntry(
            step="intake",
            summary=f"Received case {intake_record['case_id']} from {intake_record['source']}.",
            evidence={"title": intake_record["title"]},
        ),
        LiveCaseMemoryEntry(
            step="classify_case",
            summary=f"Classified as {classification['primary_type']}.",
            evidence={"categories": classification["categories"]},
        ),
        LiveCaseMemoryEntry(
            step="detect_priority",
            summary=f"Priority set to {priority['level']}.",
            evidence={"reasons": priority["reasons"]},
        ),
        LiveCaseMemoryEntry(
            step="generate_diagnostic_summary",
            summary=diagnostic_summary["summary"],
            evidence={"evidence_gaps": diagnostic_summary["evidence_gaps"]},
        ),
        LiveCaseMemoryEntry(
            step="generate_recommendation",
            summary="Generated operator-gated next actions.",
            evidence={"action_count": len(recommendation["operator_next_actions"])},
        ),
    ]
    return {
        "memory_id": f"{intake_record['case_id']}:local-memory",
        "updated_at": _now(),
        "entries": [entry.to_dict() for entry in entries],
        "persistence": "in-memory proof output; external write only when CLI output path is provided",
    }


def executive_summary(
    intake_record: dict[str, Any],
    classification: dict[str, Any],
    priority: dict[str, Any],
    diagnostic_summary: dict[str, Any],
    recommendation: dict[str, Any],
) -> str:
    first_action = recommendation["operator_next_actions"][0]
    gap_count = len(diagnostic_summary["evidence_gaps"])
    return (
        f"Case {intake_record['case_id']} is a {classification['primary_type']} "
        f"live energy operations case with {priority['level']} priority. "
        f"The runtime generated {len(diagnostic_summary['findings'])} diagnostic findings "
        f"and {gap_count} evidence gaps. Next operator action: {first_action}. "
        "No autonomous action was executed."
    )


def process_case(payload: dict[str, Any]) -> LiveCaseResult:
    intake_record = intake(payload)
    classification = classify_case(intake_record)
    priority = detect_priority(intake_record, classification)
    diagnostic_summary = generate_diagnostic_summary(
        intake_record, classification, priority
    )
    recommendation = generate_recommendation(
        intake_record, classification, priority, diagnostic_summary
    )
    memory = memory_update(
        intake_record, classification, priority, diagnostic_summary, recommendation
    )
    summary = executive_summary(
        intake_record, classification, priority, diagnostic_summary, recommendation
    )

    return LiveCaseResult(
        case_id=intake_record["case_id"],
        generated_at=_now(),
        intake=intake_record,
        classification=classification,
        priority=priority,
        diagnostic_summary=diagnostic_summary,
        recommendation=recommendation,
        memory=memory,
        executive_summary=summary,
        governance={
            "control_plane_observes": True,
            "demon_scores_later": True,
            "vma_continuity_later": True,
            "operator_decides": True,
            "ui_enabled": False,
            "cloud_enabled": False,
            "saas_enabled": False,
            "tdk_frontend_backend_integrated": False,
        },
    )


def export_json(result: LiveCaseResult) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)


def export_markdown(result: LiveCaseResult) -> str:
    payload = result.to_dict()
    findings = "\n".join(
        f"- {item}" for item in payload["diagnostic_summary"]["findings"]
    )
    gaps = "\n".join(
        f"- {item}" for item in payload["diagnostic_summary"]["evidence_gaps"]
    ) or "- none"
    actions = "\n".join(
        f"- {item}" for item in payload["recommendation"]["operator_next_actions"]
    )
    blocked = "\n".join(
        f"- {item}" for item in payload["recommendation"]["blocked_actions"]
    )
    return (
        "# LIVE CASE LOOP Report\n\n"
        f"Generated: {payload['generated_at']}\n\n"
        "## Executive Summary\n\n"
        f"{payload['executive_summary']}\n\n"
        "## Classification\n\n"
        f"- primary_type: {payload['classification']['primary_type']}\n"
        f"- categories: {', '.join(payload['classification']['categories'])}\n"
        f"- priority: {payload['priority']['level']}\n\n"
        "## Diagnostic Findings\n\n"
        f"{findings}\n\n"
        "## Evidence Gaps\n\n"
        f"{gaps}\n\n"
        "## Operator Recommendation\n\n"
        f"{actions}\n\n"
        "## Blocked Actions\n\n"
        f"{blocked}\n\n"
        "## Governance\n\n"
        "- Control Plane observes\n"
        "- DEMON scores drift/risk later\n"
        "- VMA preserves continuity later\n"
        "- Operator decides\n"
    )


def run_file(input_path: Path, output_path: Path | None = None, markdown_path: Path | None = None) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    result = process_case(payload)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(export_json(result) + "\n", encoding="utf-8")
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(export_markdown(result), encoding="utf-8")
    return result.to_dict()


def _extract_signals(payload: dict[str, Any], text: str) -> dict[str, Any]:
    lower = text.lower()
    symptoms = " ".join(payload.get("reported_symptoms", [])).lower()
    combined = f"{lower} {symptoms}"
    return {
        "critical_language": _contains_any(
            combined,
            ("awaria", "critical", "kryty", "emergency", "alarm", "pozar", "pożar"),
        ),
        "field_work_requested": _contains_any(
            combined, ("teren", "field", "serwis", "wyjazd", "instalacja")
        ),
        "economic_language": _contains_any(
            combined,
            ("koszt", "rachunek", "strata", "pln", "taryfa", "cost", "bill", "tariff", "loss"),
        ),
        "governance_language": _contains_any(
            combined, ("ai", "decyzja", "governance", "trace", "sprzeczn")
        ),
    }


def _evidence_gaps(
    intake_record: dict[str, Any], classification: dict[str, Any]
) -> list[str]:
    measurements = intake_record.get("measurements", {})
    gaps: list[str] = []
    if "pv" in classification["categories"] and "pv_production_kwh" not in measurements:
        gaps.append("pv_production_kwh")
    if "economics" in classification["categories"] and "tariff" not in measurements:
        gaps.append("tariff")
    if "ems_bess" in classification["categories"] and "battery_soc" not in measurements:
        gaps.append("battery_soc")
    if "heat_pump" in classification["categories"] and "cop" not in measurements:
        gaps.append("cop")
    if not intake_record.get("assets"):
        gaps.append("supporting_assets")
    return gaps


def _classification_confidence(
    categories: list[str], intake_record: dict[str, Any]
) -> float:
    base = 0.45 + min(len(categories), 4) * 0.1
    if intake_record.get("measurements"):
        base += 0.1
    if intake_record.get("reported_symptoms"):
        base += 0.1
    return round(min(base, 0.95), 2)


def _customer_safe_message(priority: str) -> str:
    if priority == "critical":
        return "Case requires urgent operator review before any operational action."
    if priority == "high":
        return "Case requires operator review before field recommendation."
    return "Case can proceed through standard diagnostic review."


def _max_priority(left: str, right: str) -> str:
    return left if PRIORITY_ORDER[left] >= PRIORITY_ORDER[right] else right


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _join_text(parts: list[Any]) -> str:
    return "\n".join(str(part).strip() for part in parts if str(part).strip())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Isolated LIVE CASE LOOP proof")
    parser.add_argument("--input", required=True, help="Path to live case input JSON")
    parser.add_argument("--output", default="", help="Optional JSON result path")
    parser.add_argument("--markdown", default="", help="Optional Markdown report path")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run_file(
            Path(args.input),
            Path(args.output) if args.output else None,
            Path(args.markdown) if args.markdown else None,
        )
    except Exception as exc:
        print(f"live-case-error: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
