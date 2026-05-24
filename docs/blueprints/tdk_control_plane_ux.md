# TDK Control Plane UX Blueprint

## 1. Cel panelu

TDK Control Plane ma byc lokalnym panelem operatorskim dla KODEKS / WitnessAI / EXIM / ProService. Panel nie ma zastapic istniejacych runtime'ow. Ma zlozyc je w jeden czytelny punkt kontroli: start systemu, status osi decyzyjnej, drift energii, lokalny dom, synchronizacja GitHub, raporty i gotowosc do pracy terenowej.

Glowna zasada UX: operator widzi stan systemu przed decyzja. Panel pokazuje fakty, trace, alerty i dostepne akcje. Nie wykonuje autonomicznych zmian bez potwierdzenia operatora i bez sladu runtime.

## 2. Glowne ekrany

### Start / Command Center

Pierwszy ekran po uruchomieniu Windows lub panelu. Zawiera skrot statusu:

- Local Operator Stack: running, stopped, degraded.
- Final Axis: observe, confined, operator override pending.
- DEMON_CORE: stable, observation, degraded, unstable, critical, recovery.
- GitHub sync: clean, ahead, behind, dirty, push required.
- Master System Sync: last run, report path, full scan available.
- Field readiness: docs, reports, battery/PV/EMS sample data, audit status.

### Runtime Trace

Widok decyzji i stanu Final Axis:

- ostatnie `SystemEvent`,
- trace ID,
- decyzja,
- powod,
- stan przed/po,
- confinement,
- operator override.

### Drift & Energy

Widok DEMON_CORE:

- coherence index,
- runtime entropy,
- energy loss factor,
- economic drift,
- AI conflict ratio,
- state machine,
- diagnostic findings,
- recovery plan.

### Local House / Operator Stack

Widok lokalnego domu:

- status portow: 3000, 11434, 8001, 8010, 5174, 6379, 9092, 2181,
- przyciski start/stop/monitor/backup/recovery,
- wynik `local_operator_audit`,
- ostatnie raporty w `docs/local-audits`.

### Workspace Map

Widok `master_system_sync`:

- lista repozytoriow,
- wykryte moduly DEMON / AXIS / ANCHOR / EXIM / Witness,
- uslugi Windows,
- startup apps,
- layout Desktop,
- sciezka do `C:\TDK_SYSTEM\FULL_SYSTEM_MAP.txt`.

### Field Workflow

Widok pracy terenowej ProService / TDK:

- wejscie sprawy,
- normalizacja danych,
- wybor maski / CaseReporter,
- obliczenia energetyczne,
- raport PDF / Markdown,
- zapis dowodu,
- status klient / instalacja / follow-up.

### Retina / Preview Layer

Warstwa podgladu bez wykonywania akcji:

- preview raportu,
- preview runtime logu,
- preview mapy systemu,
- preview statusu GitHub,
- preview alertu przed zatwierdzeniem operatora.

## 3. Widzety statusu

Minimalny zestaw widzetow:

- Axis State: aktualny tryb Final Axis i liczba pending override.
- Drift State: stan DEMON_CORE i najgorszy aktywny risk.
- Energy Loss: `energy_loss_factor` i `economic_drift`.
- AI Integrity: `coherence_index`, `ai_conflict_ratio`, recursive loop alert.
- Local Runtime: porty i procesy lokalnego domu.
- Audit Health: ostatni `PASS/FAIL` lokalnego audytu.
- Git Sync: branch, ahead/behind, dirty status, last commit.
- Evidence: ostatni JSONL log i Markdown report.
- Recovery: ostatni backup, dostepne recovery modes.
- Master Map: ostatni czas wykonania `master_system_sync`.

## 4. Sciezka uzytkownika od startu Windows do pracy terenowej

1. Operator uruchamia Windows.
2. Na pulpicie widzi skroty `TDK_LOCAL_HOUSE_START.bat` i `TDK_LOCAL_HOUSE_STOP.bat`.
3. Operator uruchamia lokalny dom albo otwiera Control Plane.
4. Panel sprawdza GitHub sync, status portow i ostatni runtime audit.
5. Panel pokazuje stan Final Axis i DEMON_CORE bez wykonywania zmian.
6. Operator uruchamia monitoring lub backup, jezeli status lokalnego domu nie jest zielony.
7. Operator otwiera workflow ProService / TDK.
8. Dane sprawy przechodza przez normalizacje i CaseReporter.
9. Obliczenia energetyczne sa dolaczane do procesu, jezeli sprawa jest energy case.
10. Final Axis zapisuje decyzje i trace.
11. DEMON_CORE nadzoruje drift, straty energii, konflikt AI i recovery plan.
12. Retina pokazuje preview raportu i dowodow.
13. Operator zatwierdza eksport raportu lub przechodzi do pracy terenowej.

## 5. Mapa modulow

| Warstwa | Modul | Obecna sciezka | Rola w panelu |
| --- | --- | --- | --- |
| Final Axis | `app/final_axis` | `app/final_axis` | Decyzje, confinement, semantic isometry, operator override |
| DEMON_CORE | `app/drift_energy_monitor` | `app/drift_energy_monitor` | Drift, energy continuity, economic loss, recovery plan |
| Anchor Git / AnchorGrid | `app/anchorgrid` | `app/anchorgrid` | Rdzen telemetryczno-strukturalny dla pracy Anchor / BESS |
| Process Engine | `app/engine` | `app/engine/process_engine.py` | Maski, CaseReporter, obliczenia energy case |
| Local Operator Stack | scripts + runbooks | `scripts/*local*`, `docs/runbooks/*` | Start, stop, monitor, backup, recovery, audit |
| Master System Sync | `master_system_sync.ps1` | `scripts/master_system_sync.ps1` | Mapa Windows, repo, uslug, workspace |
| API | FastAPI server | `app/api/server.py` | Lokalny endpoint administracyjny i runtime bridge |
| Reports | output layer | `app/output` | PDF, presenter, report builder |
| Session / Storage | session + storage | `app/session`, `app/storage` | Persistencja sesji, zamowienia, dane runtime |
| GitHub Sync | git state | local repo + origin/main | Publikacja zmian, kontrola historii i statusu |

## 6. Minimalny MVP dashboardu

MVP nie powinien zaczynac od ladnego UI. Najpierw powinien byc technicznym dashboardem operatorskim.

Minimalne ekrany:

- Command Center.
- Runtime Trace.
- Drift & Energy.
- Local House.
- Reports / Evidence.

Minimalne akcje:

- refresh status,
- start local house,
- stop local house,
- run local operator audit,
- run Final Axis sample,
- run DEMON_CORE sample,
- generate master system map,
- open latest report path,
- show GitHub sync status.

Minimalne dane:

- `git status --short`,
- ostatnie commity,
- status portow lokalnego domu,
- status contract zgodny z `schemas/control_plane_status.schema.json`,
- `data/final_axis/runtime_log.jsonl`,
- `data/final_axis/operational_report.md`,
- `data/drift_energy_monitor/runtime_log.jsonl`,
- `data/drift_energy_monitor/operational_report.md`,
- `docs/local-audits/local_stack_status_latest.md`,
- `C:\TDK_SYSTEM\FULL_SYSTEM_MAP.txt`, jezeli istnieje.

Minimalne ograniczenia:

- brak autonomicznego deployu,
- brak automatycznego full disk scan,
- brak automatycznego recovery bez operatora,
- brak wysylki danych poza lokalny system bez potwierdzenia.

Statusowa warstwa prawdy dla dashboardu powinna byc zgodna z kontraktem `schemas/control_plane_status.schema.json`. Panel czyta ten dokument jako read-only status plane dla `axis_runtime`, `demon_core`, `anchor_git`, `master_system_sync`, `local_operator_stack`, `proservice_workflow`, `retina_dashboard`, `github_sync` i `windows_environment`. UI moze agregowac i prezentowac te pola, ale nie powinien rozszerzac kontraktu ad hoc bez aktualizacji schematu.

## 7. Co jest aktywne teraz

Aktywne i zaimplementowane:

- Final Axis runtime prototype.
- JSONL runtime logs i Markdown operational report dla Final Axis.
- DEMON_CORE / Drift Energy Monitor.
- JSONL runtime logs i Markdown operational report dla DEMON_CORE.
- Local Operator Stack: start, stop, monitor, backup, recovery, audit.
- Master System Sync Windows map script.
- Energy case calculations w `process_engine.py`.
- AnchorGrid test coverage.
- GitHub sync: `origin/main` zawiera Final Axis, DEMON_CORE, Local Operator Stack i cleanup repo.

Aktywne jako dokumentacja/runbook:

- Local operator flow.
- Provider independence runbook.
- KODEKS local chat runbook.
- Master System Sync runbook.
- Final Axis runtime docs.
- Drift Energy Monitor docs.

Aktywne jako dane przykladowe:

- Final Axis sample PV / EMS / AI governance events.
- DEMON_CORE stable / drift / recovery snapshots.
- Generated operational reports.

## 8. Co mozna dodac pozniej bez psucia osi

Bezpieczne rozszerzenia:

- Read-only web dashboard, ktory tylko czyta JSONL, Markdown i status portow.
- `control_plane_status.py` agregujacy status modulow do jednego JSON.
- Windows tray launcher dla start/stop/monitor.
- Retina preview dla raportow i runtime logs.
- GitHub status widget bez automatycznego push.
- Operator identity w override events.
- Signed evidence export.
- Role-based confirmation dla recovery.
- Adapter do realnych EMS/PV gateway po stronie `CyberPhysicalLink`.
- DEMON_CORE live ingest z telemetrycznych CSV/JSON/API.
- AnchorGrid telemetry bridge jako osobna warstwa read-only.

Rzeczy, ktorych nie dodawac na start:

- automatyczny deploy,
- automatyczny recovery bez potwierdzenia,
- full disk scan przy starcie panelu,
- wysylka runtime logs do zewnetrznych API bez review,
- bezposrednie sterowanie EMS/PV bez Final Axis trace i BCC boundary.

Oś pozostaje stabilna, jezeli nowe elementy sa adapterami lub widokami nad istniejacymi runtime'ami, a nie zamieniaja ich reguly decyzyjne. Control Plane powinien najpierw obserwowac, potem wyjasniac, a dopiero na koncu wykonywac akcje po potwierdzeniu operatora.
