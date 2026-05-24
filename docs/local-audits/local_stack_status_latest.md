# Local Stack Status - System Zablotny Online

Timestamp: 2026-05-16 23:06 Europe/Warsaw

## Running services

- Open WebUI: http://127.0.0.1:3000
- Ollama API: http://127.0.0.1:11434
- KODEKS local API: http://127.0.0.1:8001
- KODEKS Swagger: http://127.0.0.1:8001/docs
- KODEKS Admin: http://127.0.0.1:8001/admin/orders?admin_key=test-admin
- TDK backend: http://127.0.0.1:8010
- TDK backend health: http://127.0.0.1:8010/health
- TDK backend Swagger: http://127.0.0.1:8010/docs
- TDK frontend default dev server: http://127.0.0.1:5173
- TDK frontend connected to backend 8010: http://127.0.0.1:5174

## Docker services

- open-webui: healthy, port 3000 -> 8080
- redis: port 6379
- kafka: port 9092
- zookeeper: port 2181

## Verified checks

- KODEKS local operator audit: PASS
- KODEKS PDF KPI check: PASS
- PV conservative calculation: PASS
- KODEKS local `/analyze`: generated a PDF link
- TDK backend `/health`: OK
- TDK frontend dev server: OK
- WitnessAI PDF generated: `C:\WitnessAI\WitnessAI_WhitePaper_Full.pdf`

## Notes

- KODEKS is running with local `ADMIN_KEY=test-admin`.
- TDK backend is running from `/tmp/tdk_backend_venv` on port 8010.
- TDK frontend on 5174 is the correctly connected one because it uses `VITE_API_URL=http://127.0.0.1:8010`.
- TDK frontend on 5173 is also running, but it defaults to API port 8000.
- EXIM_Witness bootstrap was inspected but not executed because it installs heavy packages and is not a runtime service.

## Stop notes

These services are local only. No deploy and no git push were performed.
