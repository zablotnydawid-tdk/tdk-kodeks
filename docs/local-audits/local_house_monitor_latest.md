# Local House Monitor

- Timestamp: 2026-05-21T16:59:15
- Root: /mnt/c/KODEKS

## HTTP

- [OK] Open WebUI (http://127.0.0.1:3000/): HTTP 200, 300 bytes sample
- [OK] Ollama tags (http://127.0.0.1:11434/api/tags): HTTP 200, 300 bytes sample
- [OK] KODEKS API (http://127.0.0.1:8001/): HTTP 200, 300 bytes sample
- [OK] KODEKS Swagger (http://127.0.0.1:8001/docs): HTTP 200, 300 bytes sample
- [OK] KODEKS Admin (http://127.0.0.1:8001/admin/orders?admin_key=test-admin): HTTP 200, 300 bytes sample
- [OK] TDK backend health (http://127.0.0.1:8010/health): HTTP 200, 217 bytes sample
- [OK] TDK backend Swagger (http://127.0.0.1:8010/docs): HTTP 200, 300 bytes sample
- [OK] TDK frontend connected (http://127.0.0.1:5174/): HTTP 200, 300 bytes sample

## Ports

- [OK] Open WebUI: 127.0.0.1:3000
- [OK] Ollama: 127.0.0.1:11434
- [OK] KODEKS API: 127.0.0.1:8001
- [OK] TDK backend: 127.0.0.1:8010
- [OK] TDK frontend connected: 127.0.0.1:5174
- [OK] Redis: 127.0.0.1:6379
- [OK] Kafka: 127.0.0.1:9092
- [OK] Zookeeper: 127.0.0.1:2181

## Ollama Models

- llama3.2:3b
- phi3:mini
- llama3.2:1b
- llama3:latest
- tdk-proservice-v2:latest
- tdk-proservice:latest
- pv-hp-asystent:latest
- my-model-name:latest

## KODEKS Operator Audit

- [OK] local_operator_audit.py --no-write

```text
  ?? tests/

- [OK] directory data/orders
- [OK] directory data/reports
- [OK] directory docs
- [OK] py_compile core flow: app/engine/steps.py, app/engine/process_engine.py, app/output/report_builder.py
- [OK] PV conservative calculation: {'cost_without_pv': 2621.13, 'raw_cost_after_pv': 0.0, 'residual_cost_floor': 524.23, 'cost_after_pv': 524.23, 'savings': 2096.9, 'efficiency_label': 'wysoka efektywność', 'calculation_mode': 'conservative_residual_estimate'}
- [OK] engine -> report cost_after_pv: cost_after_pv=524.23
- [OK] PDF KPI PO PV source: {'cost_without_pv': '2621.13 zł', 'cost_after_pv': '524.23 zł', 'savings': '2096.9 zł'}

## Result
PASS
```

## Result

PASS
