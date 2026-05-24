# Local Runtime Audit - TDK/KODEKS Offline-First

Date: 2026-05-16
Mode: local runtime baseline, no deploy, no git push

## Executive Summary

Lokalny stack TDK/KODEKS dziala jako niezalezny runtime offline-first dla pracy operatora.
Krytyczne elementy sa uruchomione lokalnie: Open WebUI, Ollama, KODEKS API,
TDK backend, TDK frontend, lokalna generacja PDF oraz lokalne modele.

Najwazniejszy test wiarygodnosci PV przeszedl:

```text
PO PV = 524.23 zl
cost_after_pv != 0
PV/PDF KPI = PASS
```

Produkcja cloud nie byla dotykana.
Render, Vercel, DNS, SMTP i sekrety produkcyjne pozostaly bez zmian.

## Architektura Lokalna

```text
Windows / WSL host
  |
  |-- Docker
  |     |-- Open WebUI :3000
  |     |-- Redis :6379
  |     |-- Kafka :9092
  |     |-- Zookeeper :2181
  |
  |-- Ollama :11434
  |     |-- local LLM models
  |
  |-- KODEKS FastAPI :8001
  |     |-- engine
  |     |-- report_builder
  |     |-- pdf_builder
  |     |-- data/orders
  |     |-- data/reports
  |
  |-- TDK Backend FastAPI :8010
  |     |-- SQLite app.db
  |     |-- auth/modules/subscriptions/gpt_bridge
  |
  |-- TDK Front Vite :5174
        |-- VITE_API_URL=http://127.0.0.1:8010
```

## Aktywne Porty

| Port | Usluga | Status | Uwagi |
| --- | --- | --- | --- |
| 3000 | Open WebUI | OK | Docker, mapuje 3000 -> 8080 |
| 11434 | Ollama API | OK | lokalne modele aktywne |
| 8001 | KODEKS API | OK | `ADMIN_KEY=test-admin` |
| 8010 | TDK backend | OK | uruchomiony z `/tmp/tdk_backend_venv` |
| 5174 | TDK frontend | OK | poprawnie spiety z backendem 8010 |
| 5173 | TDK frontend default | OK | dziala, ale domyslnie celuje w API 8000 |
| 6379 | Redis | OK | Docker |
| 9092 | Kafka | OK | Docker |
| 2181 | Zookeeper | OK | Docker |

## Aktywne Uslugi

- Open WebUI: `http://127.0.0.1:3000`
- Ollama: `http://127.0.0.1:11434`
- KODEKS API: `http://127.0.0.1:8001`
- KODEKS Swagger: `http://127.0.0.1:8001/docs`
- KODEKS Admin: `http://127.0.0.1:8001/admin/orders?admin_key=test-admin`
- TDK backend: `http://127.0.0.1:8010`
- TDK backend health: `http://127.0.0.1:8010/health`
- TDK backend Swagger: `http://127.0.0.1:8010/docs`
- TDK frontend connected: `http://127.0.0.1:5174`
- TDK frontend default: `http://127.0.0.1:5173`

## Lista Modeli Ollama

- `llama3.2:3b`
- `phi3:mini`
- `llama3.2:1b`
- `llama3:latest`
- `tdk-proservice-v2:latest`
- `tdk-proservice:latest`
- `pv-hp-asystent:latest`
- `my-model-name:latest`

## Flow Danych KODEKS

```text
formularz / API
  -> app.api.server.run_analysis()
  -> app.input.normalizer.normalize_input()
  -> app.routing.mask_router.choose_mask()
  -> app.engine.process_engine.run_process()
  -> app.engine.steps.calculate_energy_case()
  -> process_result["calculations"]
  -> app.output.report_builder.build_report()
  -> app.output.pdf_builder.generate_pdf()
  -> data/reports/*.pdf
  -> /reports/{file}.pdf
```

## Status Frontend -> Backend -> Engine -> PDF

KODEKS:

- `GET /` odpowiada HTML formularza.
- `GET /docs` odpowiada Swagger UI.
- `GET /admin/orders?admin_key=test-admin` odpowiada panelem admina.
- `POST /analyze` wygenerowal lokalny PDF:
  `http://127.0.0.1:8001/reports/raport_20260516_231322_c60a6ecc.pdf`

TDK:

- TDK backend `/health` zwraca `{"status":"ok"}`.
- TDK backend Swagger dziala.
- TDK frontend na `5174` serwuje aplikacje Vite.
- Frontend `5174` jest poprawnym lokalnym wariantem, bo ma `VITE_API_URL=http://127.0.0.1:8010`.

## Flow Ollama -> Open WebUI -> Modele Lokalne

- Ollama odpowiada przez `http://127.0.0.1:11434/api/tags`.
- Open WebUI jest uruchomione przez Docker pod `http://127.0.0.1:3000`.
- Modele lokalne sa widoczne przez API Ollama.
- Ten flow dziala bez Render/Vercel i bez zewnetrznego API modelowego.

## Status PDF

- Lokalna generacja PDF KODEKS dziala.
- PDF zapisuje sie do `data/reports/`.
- PDF jest serwowany lokalnie przez `/reports/{filename}`.
- `pdf_builder` pobiera KPI z tekstu raportu.
- `report_builder` otrzymuje finalne `process_result["calculations"]`.

## Status PV Engine

Krytyczny test:

```text
consumption_kwh = 2131
price_per_kwh = 1.23
pv_monthly_production_kwh = 4321
```

Wynik:

```text
cost_without_pv = 2621.13
raw_cost_after_pv = 0.0
residual_cost_floor = 524.23
cost_after_pv = 524.23
savings = 2096.9
efficiency_label = wysoka efektywnosc
calculation_mode = conservative_residual_estimate
```

Status:

```text
PV conservative calculation = PASS
engine -> report cost_after_pv = PASS
PDF KPI PO PV = 524.23 zl = PASS
```

## Status Admin

- Admin lokalny dziala pod:
  `http://127.0.0.1:8001/admin/orders?admin_key=test-admin`
- Istniejace ordery z `pdf_url` nie generuja PDF drugi raz.
- To zachowuje manualny flow platnosci i chroni przed nadpisywaniem raportow.

## Status Swagger

- KODEKS Swagger: OK
- TDK backend Swagger: OK

## Cache / Build / Runtime Scan

Wykryte katalogi runtime/cache:

- `.venv/` - lokalne zaleznosci KODEKS, okolo 83 MB.
- `build/` - artefakty PyInstaller, okolo 11 MB.
- `dist/` - artefakty exe, okolo 8.2 MB.
- `data/` - lokalne dane, okolo 1.2 MB.
- `__pycache__/` - wiele katalogow cache Python.
- `docs/local-audits/` - lokalne raporty audytowe.

Wykryte dane poza KODEKS:

- `/mnt/c/TDK/TDK_backend/database/app.db` - lokalna baza SQLite TDK backend.
- `/mnt/c/TDK/TDK_front/.env` - lokalny ENV frontu.
- `/mnt/c/WitnessAI/*.pdf` - lokalne PDF WitnessAI.

## Git Hygiene

Naprawiono `.gitignore`, ktory byl uszkodzony bajtowo/nullami.
Nowy `.gitignore` chroni:

- `.venv/`
- `__pycache__/`
- `.env`
- `data/orders/*.json`
- `data/sessions/*.json`
- `data/reports/*.pdf`
- `data/reports/*.txt`
- `docs/local-audits/*.md` z wyjatkiem dokumentow baseline
- `build/`
- `dist/`
- `*.spec`
- `node_modules/`
- `.vite/`
- logi i temp files

Wazne:

Niektore dane i build artefakty sa juz historycznie sledzone przez git, wiec `.gitignore`
nie usuwa ich automatycznie z indeksu. To wymaga osobnej, swiadomej operacji
`git rm --cached`, ktorej ten audyt nie wykonuje.

## Katalogi Ktore NIE Powinny Trafiac Do Repo

- `.venv/`
- `venv/`
- `node_modules/`
- `.vite/`
- `build/`
- `dist/`
- `__pycache__/`
- `.pytest_cache/`
- `data/reports/*.pdf`
- `data/reports/*.txt`
- `data/orders/*.json`
- `data/sessions/*.json`
- `docs/local-audits/local_operator_audit_*.md`
- lokalne `.env`
- lokalne `.db` / `.sqlite`, jesli zawieraja dane runtime

## Runtime-Only

- KODEKS `.venv/`
- TDK backend `/tmp/tdk_backend_venv`
- Open WebUI container
- Redis/Kafka/Zookeeper containers
- Ollama service
- lokalne PDF w `data/reports/`
- lokalne JSON orders/sessions
- TDK backend `database/app.db`
- WitnessAI wygenerowane PDF

## Dev-Only

- `scripts/local_operator_audit.py`
- `scripts/run_local_operator_audit.ps1`
- `docs/runbooks/local-operator-flow.md`
- `docs/system-zablotny-online.md`
- `docs/local-audits/local_runtime_audit.md`
- `docs/local-audits/local_stack_status_latest.md`
- `.env.example`
- `requirements.txt`

## Dane Lokalne

- `data/orders/`
- `data/reports/`
- `data/sessions/`
- `docs/local-audits/`
- `/mnt/c/TDK/TDK_backend/database/app.db`
- `/mnt/c/TDK/TDK_front/.env`
- `/mnt/c/WitnessAI/*.pdf`

## Ryzyka

1. Tracked runtime files

Repo historycznie sledzi czesc plikow z `data/`, `build/`, `dist/` i `gui.spec`.
To jest ryzyko przypadkowego commita danych lokalnych.

2. Dwa frontendy TDK

Port `5173` dziala, ale domyslnie celuje w API `localhost:8000`.
Port `5174` jest poprawnym lokalnym frontendem spietym z backendem `8010`.

3. Lokalny order z dawnym base_url

`data/orders/KODEKS-20260516-0655E4.json` zawiera lokalny URL `127.0.0.1:8000`.
To jest historyczny runtime data, nie blad aktualnego stacku.

4. SMTP nadal nie jest fundamentem offline-first

Mail pozostaje dodatkiem. Lokalny runtime nie powinien opierac krytycznego flow na SMTP.

5. TDK backend venv w katalogu projektu byl uszkodzony

`/mnt/c/TDK/TDK_backend/.venv` mial uszkodzony pip. Backend uruchomiono bezpiecznie
z `/tmp/tdk_backend_venv`.

6. EXIM_Witness bootstrap_local.py

Plik instaluje ciezkie pakiety (`whisper`, `openai`, `edge-tts`, `pyttsx3`).
Nie jest runtime service i nie powinien byc odpalany automatycznie bez decyzji.

7. Open WebUI zalezy od kontenera Docker

Offline-first dziala lokalnie, ale wymaga dzialajacego Docker Desktop/WSL stack.

## Rekomendacje

1. W osobnym kroku oczyscic indeks git z runtime data:

```bash
git rm --cached -r build dist
git rm --cached data/reports/*.pdf
git rm --cached data/reports/*.txt
git rm --cached data/orders/*.json
git rm --cached data/sessions/*.json
```

Tego nie wykonywac bez osobnej decyzji, bo zmieni stan repo.

2. Ustandaryzowac porty:

```text
3000 - Open WebUI
8001 - KODEKS API
8010 - TDK backend
5174 - TDK frontend connected
11434 - Ollama
```

3. Nie uzywac frontendu `5173` jako glownego lokalnego wejscia.

4. Dodac docelowo skrypt `start_local_house.ps1`, ktory:

- sprawdza Docker,
- sprawdza Ollama,
- uruchamia KODEKS,
- uruchamia TDK backend,
- uruchamia TDK frontend z `VITE_API_URL`,
- odpala `local_operator_audit.py`.

5. Dodac skrypt `stop_local_house.ps1`, ale dopiero po opisaniu PID/session handling.

6. Dla produkcyjnego storage nadal priorytetem zostaje Supabase/PostgreSQL + trwaly PDF storage.

## Automatyzacja Operacyjna

Dodane skrypty lokalnego domu:

- `scripts/start_local_house.ps1` - uruchamia Docker containers, KODEKS API, TDK backend i TDK frontend.
- `scripts/stop_local_house.ps1` - zatrzymuje lokalne aplikacje na portach 8001, 8010 i 5174; opcjonalnie Docker infra przez `-IncludeInfra`.
- `scripts/backup_local_house.ps1` - tworzy backup KODEKS app/docs/scripts/config, orders/reports, TDK SQLite, TDK front `.env` i WitnessAI PDF.
- `scripts/recover_local_house.ps1` - odtwarza kod i/lub runtime data z backupu; domyslnie dziala jako dry-run.
- `scripts/monitor_local_house.ps1` - uruchamia monitoring lokalnego domu.
- `scripts/local_house_status.py` - sprawdza HTTP, porty, modele Ollama i audyt operatora.

Monitoring latest:

```text
docs/local-audits/local_house_monitor_latest.md
```

## Backup Checklist

Przed wiekszymi zmianami skopiowac:

- `app/`
- `docs/`
- `scripts/`
- `.env.example`
- `requirements.txt`
- `render.yaml`
- `data/orders/`
- `data/reports/`
- `/mnt/c/TDK/TDK_backend/database/app.db`
- `/mnt/c/TDK/TDK_front/.env`

Minimalny backup runtime:

```text
KODEKS app + docs + scripts + data/orders + data/reports
TDK_backend database/app.db
TDK_front .env
Ollama model list
```

## Recovery Checklist

1. Uruchom Docker Desktop / WSL.
2. Sprawdz Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
```

3. Sprawdz Open WebUI:

```text
http://127.0.0.1:3000
```

4. Wejdz do KODEKS:

```bash
cd /mnt/c/KODEKS
```

5. Jesli nie ma `.venv`, odtworz:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

6. Uruchom KODEKS:

```bash
ADMIN_KEY=test-admin .venv/bin/python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8001
```

7. Uruchom TDK backend:

```bash
cd /mnt/c/TDK/TDK_backend
python3 -m venv /tmp/tdk_backend_venv
/tmp/tdk_backend_venv/bin/python -m pip install -r requirements.txt
PORT=8010 /tmp/tdk_backend_venv/bin/python main.py
```

8. Uruchom TDK frontend:

```bash
cd /mnt/c/TDK/TDK_front
VITE_API_URL=http://127.0.0.1:8010 npm run dev -- --host 127.0.0.1 --port 5174
```

9. Uruchom audyt:

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/local_operator_audit.py
```

## Startup Checklist

1. Open WebUI: `http://127.0.0.1:3000`
2. Ollama tags: `http://127.0.0.1:11434/api/tags`
3. KODEKS Swagger: `http://127.0.0.1:8001/docs`
4. KODEKS Admin: `http://127.0.0.1:8001/admin/orders?admin_key=test-admin`
5. TDK backend health: `http://127.0.0.1:8010/health`
6. TDK frontend: `http://127.0.0.1:5174`
7. Local audit: `PASS`
8. PV/PDF KPI: `PO PV = 524.23 zl`

## Minimalna Procedura Odzyskania Systemu Po Awarii Windows

1. Uruchomic Windows i Docker Desktop.
2. Uruchomic WSL/terminal.
3. Sprawdzic, czy Docker kontenery wstaly:

```bash
docker ps
```

4. Sprawdzic Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
```

5. Jesli Ollama nie dziala, uruchomic usluge Ollama ponownie z poziomu Windows/WSL.
6. Przejsc do KODEKS i uruchomic backend lokalny:

```bash
cd /mnt/c/KODEKS
ADMIN_KEY=test-admin .venv/bin/python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8001
```

7. Przejsc do TDK backend i uruchomic:

```bash
cd /mnt/c/TDK/TDK_backend
PORT=8010 /tmp/tdk_backend_venv/bin/python main.py
```

8. Przejsc do TDK frontend i uruchomic:

```bash
cd /mnt/c/TDK/TDK_front
VITE_API_URL=http://127.0.0.1:8010 npm run dev -- --host 127.0.0.1 --port 5174
```

9. Otworzyc:

```text
http://127.0.0.1:3000
http://127.0.0.1:8001/docs
http://127.0.0.1:5174
```

10. Uruchomic audyt:

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/local_operator_audit.py
```

System jest odzyskany, jesli audyt zwraca `PASS`.

## Jak Uruchomic Caly Lokalny Dom W Mniej Niz 5 Minut

Terminal 1 - KODEKS:

```bash
cd /mnt/c/KODEKS
ADMIN_KEY=test-admin .venv/bin/python -m uvicorn app.api.server:app --host 127.0.0.1 --port 8001
```

Terminal 2 - TDK backend:

```bash
cd /mnt/c/TDK/TDK_backend
PORT=8010 /tmp/tdk_backend_venv/bin/python main.py
```

Terminal 3 - TDK frontend:

```bash
cd /mnt/c/TDK/TDK_front
VITE_API_URL=http://127.0.0.1:8010 npm run dev -- --host 127.0.0.1 --port 5174
```

Terminal 4 - audyt:

```bash
cd /mnt/c/KODEKS
.venv/bin/python scripts/local_operator_audit.py
```

Wejscia:

```text
Open WebUI: http://127.0.0.1:3000
KODEKS: http://127.0.0.1:8001
TDK frontend: http://127.0.0.1:5174
```

## Baseline

Aktualny stan nalezy traktowac jako stabilny baseline lokalnej pracy.
Nie usuwac procesow i nie zmieniac portow bez aktualizacji tego dokumentu.
