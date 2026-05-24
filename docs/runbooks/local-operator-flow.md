# Local Operator Flow

## Cel

Ten runbook uruchamia lokalny audyt operatora bez dotykania produkcji, Render, DNS,
SMTP, endpointow ani flow platnosci.

## Uruchomienie na Windows PowerShell

```powershell
cd C:\KODEKS
.\scripts\run_local_operator_audit.ps1
```

## Pelny lokalny dom

Najprostszy tryb:

```text
Pulpit -> TDK_LOCAL_HOUSE_START.bat
```

Stop:

```text
Pulpit -> TDK_LOCAL_HOUSE_STOP.bat
```

Start calego lokalnego runtime:

```powershell
cd C:\KODEKS
.\scripts\start_local_house.ps1
```

Monitoring:

```powershell
cd C:\KODEKS
.\scripts\monitor_local_house.ps1
```

Backup:

```powershell
cd C:\KODEKS
.\scripts\backup_local_house.ps1
```

Stop aplikacji lokalnych:

```powershell
cd C:\KODEKS
.\scripts\stop_local_house.ps1
```

Stop aplikacji lokalnych razem z kontenerami Docker:

```powershell
cd C:\KODEKS
.\scripts\stop_local_house.ps1 -IncludeInfra
```

Recovery dry-run:

```powershell
cd C:\KODEKS
.\scripts\recover_local_house.ps1 -BackupPath C:\KODEKS\backups\local_house_YYYYMMDD_HHMMSS
```

Recovery kodu:

```powershell
cd C:\KODEKS
.\scripts\recover_local_house.ps1 -BackupPath C:\KODEKS\backups\local_house_YYYYMMDD_HHMMSS -RestoreCode
```

Recovery danych runtime:

```powershell
cd C:\KODEKS
.\scripts\recover_local_house.ps1 -BackupPath C:\KODEKS\backups\local_house_YYYYMMDD_HHMMSS -RestoreRuntimeData
```

## Uruchomienie z WSL / bash

```bash
cd /mnt/c/KODEKS
python3 scripts/local_operator_audit.py
```

## Co sprawdza automatyzacja

- status git,
- istnienie katalogow `data/orders`, `data/reports`, `docs`,
- skladnie kluczowego flow: `steps.py`, `process_engine.py`, `report_builder.py`,
- czy `calculate_energy_case()` nie zwraca `cost_after_pv = 0` dla przypadku nadprodukcji PV,
- czy `run_process()` przekazuje finalne `cost_after_pv` do `report_builder`,
- czy KPI PDF pobiera `PO PV = 524.23 zl`, jesli lokalnie jest dostepny ReportLab.

## Raport

Kazde uruchomienie zapisuje raport w:

```text
docs/local-audits/
```

Mozna uruchomic bez zapisu:

```bash
python3 scripts/local_operator_audit.py --no-write
```

## Krytyczny test PV

Dane testowe:

```text
consumption_kwh = 2131
price_per_kwh = 1.23
pv_monthly_production_kwh = 4321
```

Oczekiwane:

```text
cost_without_pv = 2621.13
raw_cost_after_pv = 0.0
residual_cost_floor = 524.23
cost_after_pv = 524.23
savings = 2096.9
calculation_mode = conservative_residual_estimate
```

## Zasada

Jesli audyt zwraca `FAIL`, nie robic deployu przed wyjasnieniem przyczyny.

## Standard portow lokalnego domu

```text
3000  Open WebUI
11434 Ollama
8001  KODEKS API
8010  TDK backend
5174  TDK frontend connected
6379  Redis
9092  Kafka
2181  Zookeeper
```

## Pliki operacyjne

- `C:\KODEKS\TDK_LOCAL_HOUSE_START.bat`
- `C:\KODEKS\TDK_LOCAL_HOUSE_STOP.bat`
- `C:\Users\zablo\Desktop\TDK_LOCAL_HOUSE_START.bat`
- `C:\Users\zablo\Desktop\TDK_LOCAL_HOUSE_STOP.bat`
- `scripts/start_local_house_wsl.sh`
- `scripts/stop_local_house_wsl.sh`
- `scripts/start_local_house.ps1`
- `scripts/stop_local_house.ps1`
- `scripts/backup_local_house.ps1`
- `scripts/recover_local_house.ps1`
- `scripts/monitor_local_house.ps1`
- `scripts/local_house_status.py`
- `scripts/local_operator_audit.py`

## Raporty stabilizacji

- `docs/local-audits/local_runtime_audit.md`
- `docs/local-audits/local_stack_status_latest.md`
- `docs/local-audits/local_house_monitor_latest.md`
