from src.acpc.ingest import ACPCLiveIngestGateway, replay_wal
from src.acpc.ingest.replay import replay_events

def test_mqtt_normalization_and_wal(tmp_path):
    g = ACPCLiveIngestGateway(wal_path=str(tmp_path / "wal.log"))
    e = g.ingest({"power_kw": 4.5, "inv_temp_c": 42.1}, "MQTT", "SITE_A")
    assert e.metrics["dc_power_w"] == 4500.0
    assert e.metrics["temp_inverter_c"] == 42.1
    assert len(list(g.wal.read_all())) == 1

def test_modbus_normalization(tmp_path):
    g = ACPCLiveIngestGateway(wal_path=str(tmp_path / "wal.log"))
    e = g.ingest({"reg_40083": 4450, "reg_40103": 43.5}, "MODBUS_TCP", "SITE_B")
    assert e.metrics["dc_power_w"] == 4450.0
    assert e.metrics["temp_inverter_c"] == 43.5

def test_deterministic_replay_independent_of_input_order(tmp_path):
    g = ACPCLiveIngestGateway(wal_path=str(tmp_path / "wal.log"))
    e1 = g.ingest({"power_kw": 1, "inv_temp_c": 30}, "MQTT", "SITE_A", timestamp=100)
    e2 = g.ingest({"power_kw": 2, "inv_temp_c": 31}, "MQTT", "SITE_A", timestamp=101)
    assert replay_events([e1, e2])["SITE_A"].metrics == replay_events([e2, e1])["SITE_A"].metrics

def test_replay_wal_restores_state(tmp_path):
    wal = tmp_path / "wal.log"
    g = ACPCLiveIngestGateway(wal_path=str(wal))
    g.ingest({"power_kw": 3.2, "inv_temp_c": 40}, "MQTT", "SITE_A")
    state = replay_wal(str(wal))
    assert state["SITE_A"].metrics["dc_power_w"] == 3200.0
    assert state["SITE_A"].event_count == 1
