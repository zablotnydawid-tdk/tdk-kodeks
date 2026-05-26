
from src.acpc.energy.pv_diagnostics import PVDiagnosticEngine
from src.acpc.energy.pv_diagnostics.models import PVEvent, PVEventType


def sample():
    return {
      "site_id": "PV-Krakow-A",
      "system_kwp": "dziesiec",
      "inverter": "Growatt",
      "strings": [
        {"id": "S-jeden", "voltage_v": "siedemset dwadziescia", "current_a": "osiem przecinek cztery", "power_w": "szesc tysiecy czterdziesci osiem"},
        {"id": "S-dwa", "voltage_v": "szescset dziewiecdziesiat", "current_a": "szesc przecinek jeden", "power_w": "cztery tysiace dwiescie dziewiec"}
      ],
      "daily_yield_kwh": "trzydziesci dwa przecinek piec",
      "expected_yield_kwh": "czterdziesci jeden przecinek zero",
      "module_temperature_c": "siedemdziesiat dwa",
      "insulation_mohm": "jeden przecinek dwa",
      "witness_mode": True,
    }


def test_spadek_uzysku_i_pid_krytyczny():
    engine = PVDiagnosticEngine("PV-Krakow-A")
    state = engine.apply(PVEvent(PVEventType.PV_SAMPLE_RECEIVED, sample(), "PV-Krakow-A", lamport=1, event_id="e1"))
    assert state.status.value == "critical"
    assert "request_thermal_scan" in state.actions
    assert "insulation_test" in state.actions
    assert any(f.id == "pid_risk" for f in state.findings)


def test_idempotent_event():
    engine = PVDiagnosticEngine("PV-Krakow-A")
    event = PVEvent(PVEventType.PV_SAMPLE_RECEIVED, sample(), "PV-Krakow-A", lamport=1, event_id="same")
    engine.apply(event)
    engine.apply(event)
    assert len(engine.state.samples) == 1
    assert len(engine.state.processed_event_ids) == 1


def test_deterministic_replay_ordering():
    events = [
        PVEvent(PVEventType.DIAGNOSIS_CONFIRMED, {"witness_mode": True}, "PV-Krakow-A", lamport=2, event_id="e2"),
        PVEvent(PVEventType.PV_SAMPLE_RECEIVED, sample(), "PV-Krakow-A", lamport=1, event_id="e1"),
    ]
    a = PVDiagnosticEngine("PV-Krakow-A"); a.replay(events)
    b = PVDiagnosticEngine("PV-Krakow-A"); b.replay(list(reversed(events)))
    assert a.json_report() == b.json_report()


def test_zakonczenie_diagnozy_generuje_raport():
    engine = PVDiagnosticEngine("PV-Krakow-A")
    engine.apply(PVEvent(PVEventType.PV_SAMPLE_RECEIVED, sample(), "PV-Krakow-A", lamport=1, event_id="e1"))
    state = engine.apply(PVEvent(PVEventType.DIAGNOSIS_CONFIRMED, {"witness_mode": True}, "PV-Krakow-A", lamport=2, event_id="e2"))
    assert state.status.value == "resolved"
    assert "generate_markdown_json_report" in state.actions
    report = engine.json_report()
    assert report["report_type"] == "PV_DIAGNOSTIC_REPORT"
    assert report["witness_mode"]["intervention_logged"] == "tak"
