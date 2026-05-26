
from __future__ import annotations
from typing import Dict, List, Tuple
from .models import PVEvent, PVEventType, PVInstallationState, PVState
from .rules import evaluate_pv_rules


TRANSITIONS: Dict[tuple[PVState, PVEventType], tuple[PVState, List[str]]] = {
    (PVState.IDLE, PVEventType.PV_SAMPLE_RECEIVED): (PVState.COLLECTING_DATA, ["normalize_sample", "evaluate_baseline"]),
    (PVState.COLLECTING_DATA, PVEventType.YIELD_DROP_DETECTED): (PVState.ANALYZING, ["compare_strings", "check_weather", "request_thermal_scan"]),
    (PVState.ANALYZING, PVEventType.PID_SUSPECTED): (PVState.CRITICAL, ["insulation_test", "el_measurement", "lock_service_case"]),
    (PVState.ANALYZING, PVEventType.MPI_SUSPECTED): (PVState.WARNING, ["iv_curve_test", "check_connectors", "check_shading"]),
    (PVState.WARNING, PVEventType.PID_SUSPECTED): (PVState.CRITICAL, ["insulation_test", "el_measurement", "lock_service_case"]),
    (PVState.WARNING, PVEventType.THERMAL_SCAN_ATTACHED): (PVState.ANALYZING, ["evaluate_hotspots", "attach_evidence"]),
    (PVState.CRITICAL, PVEventType.THERMAL_SCAN_ATTACHED): (PVState.CRITICAL, ["evaluate_hotspots", "attach_evidence"]),
    (PVState.ANALYZING, PVEventType.DIAGNOSIS_CONFIRMED): (PVState.RESOLVED, ["generate_markdown_json_report"]),
    (PVState.WARNING, PVEventType.DIAGNOSIS_CONFIRMED): (PVState.RESOLVED, ["generate_markdown_json_report"]),
    (PVState.CRITICAL, PVEventType.DIAGNOSIS_CONFIRMED): (PVState.RESOLVED, ["generate_markdown_json_report"]),
}


def reduce_event(state: PVInstallationState, event: PVEvent) -> PVInstallationState:
    eid = event.stable_id()
    if eid in state.processed_event_ids:
        return state

    state.processed_event_ids.add(eid)
    state.lamport_clock = max(state.lamport_clock, event.lamport) + 1

    if event.event_type == PVEventType.PV_SAMPLE_RECEIVED:
        state.samples.append(event.payload)
        findings = evaluate_pv_rules(event.payload)
        _merge_findings(state, findings)
        if findings:
            if any(f.id == "yield_drop" for f in findings):
                state.status = PVState.ANALYZING
                state.actions.extend(["compare_strings", "check_weather", "request_thermal_scan"])
            if any(f.severity == "critical" for f in findings):
                state.status = PVState.CRITICAL
                state.actions.extend(["insulation_test", "el_measurement", "thermal_inspection"])
            elif state.status != PVState.CRITICAL:
                state.status = PVState.WARNING
        else:
            state.status = PVState.COLLECTING_DATA

    elif event.event_type == PVEventType.INVERTER_ALARM_RECEIVED:
        state.inverter_alarms.append(event.payload)
        state.status = PVState.WARNING if state.status != PVState.CRITICAL else state.status
        state.actions.append("check_inverter_alarm")

    elif event.event_type == PVEventType.THERMAL_SCAN_ATTACHED:
        state.thermal_scans.append(event.payload)
        if state.samples:
            _merge_findings(state, evaluate_pv_rules(state.samples[-1], event.payload))
        state.actions.extend(["evaluate_hotspots", "attach_evidence"])
        if any(f.id == "hotspot" for f in state.findings):
            state.status = PVState.CRITICAL

    else:
        next_state, actions = TRANSITIONS.get((state.status, event.event_type), (state.status, []))
        state.status = next_state
        state.actions.extend(actions)

        if event.event_type == PVEventType.PID_SUSPECTED:
            state.status = PVState.CRITICAL
            state.actions.extend(["insulation_test", "el_measurement"])
        if event.event_type == PVEventType.MPI_SUSPECTED and state.status != PVState.CRITICAL:
            state.status = PVState.WARNING
            state.actions.extend(["iv_curve_test", "check_connectors"])
        if event.event_type == PVEventType.DIAGNOSIS_CONFIRMED:
            state.status = PVState.RESOLVED
            state.actions.append("generate_markdown_json_report")

    if event.payload.get("witness_mode"):
        state.witness_log.append({
            "event_id": eid,
            "event_type": event.event_type.value,
            "site_id": event.site_id,
            "lamport_after": state.lamport_clock,
            "intervention_logged": "tak",
            "signature": event.payload.get("signature", "WitnessAI Serwis OZE"),
            "location_required": "tak",
        })

    # deterministic de-dup action order
    state.actions = list(dict.fromkeys(state.actions))
    return state


def _merge_findings(state: PVInstallationState, findings):
    by_id = {f.id: f for f in state.findings}
    for f in findings:
        by_id[f.id] = f
    state.findings = [by_id[k] for k in sorted(by_id)]
