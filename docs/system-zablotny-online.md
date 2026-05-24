# System Zablotny Online - lokalna warstwa operacyjna TDK&ProService

## Status

Dokument inicjalny. Nie jest to wdrozenie produkcyjne ani przebudowa KODEKS.
To plan utworzenia lokalnej warstwy operacyjnej nad Windows i obecnym projektem.

## Cel

System Zablotny Online ma ograniczyc zaleznosc pracy TDK&ProService od:

- limitow tokenow,
- usypiania hostingu,
- utraty kontekstu,
- timeoutow cloud,
- rozproszonej dokumentacji,
- pojedynczego dostawcy AI,
- recznego odtwarzania decyzji projektowych.

System nie zastepuje Windows. Windows pozostaje hostem.
System Zablotny Online ma byc warstwa nadrzedna pracy:

```text
Windows host
-> lokalny runtime TDK/Witness
-> KODEKS engine
-> pamiec projektu
-> pipeline dokumentow
-> opcjonalne modele lokalne/cloud
-> GUI operatora
```

## Zasada nadrzedna

Najpierw stabilnosc i pamiec. Dopiero potem automatyzacja.

Nie wolno przebudowywac dzialajacego MVP tylko dlatego, ze powstaje nowa warstwa.
KODEKS produkcyjny pozostaje systemem sprzedazowym, a lokalna warstwa ma go wzmacniac.

## Warstwy systemu

### 1. Local Runtime

Odpowiada za uruchamianie procesow lokalnych:

- backend FastAPI,
- lokalne testy,
- generowanie PDF,
- walidacje danych,
- zadania cykliczne,
- diagnostyke repozytorium.

Minimalny kierunek:

```text
scripts/
  run_local_api.ps1
  run_tests.ps1
  generate_preview_pdf.ps1
  audit_workspace.ps1
```

### 2. Project Memory

Odpowiada za trwala pamiec decyzji, bledow i flow.

Minimalny kierunek:

```text
docs/
  master-operational-state.md
  system-zablotny-online.md
  decisions/
  incidents/
  runbooks/
```

Docelowo:

- SQLite lokalnie,
- eksport do JSON/Markdown,
- pozniej opcjonalnie wektorowa pamiec lokalna.

### 3. Knowledge Layer

Warstwa wiedzy technicznej TDK&ProService:

- fotowoltaika,
- pompy ciepla,
- magazyny energii,
- faktury,
- taryfy,
- rozliczenia prosumentow,
- diagnostyka bledow,
- wzorce raportow.

Minimalny kierunek:

```text
knowledge/
  pv/
  heat-pumps/
  tariffs/
  invoices/
  reports/
```

### 4. Orchestrator

Warstwa, ktora decyduje, co uruchomic:

- audyt kodu,
- generowanie raportu,
- walidacje PDF,
- sprawdzenie orderow,
- przygotowanie deployment checklist,
- eksport dokumentacji.

Na poczatku moze to byc prosta aplikacja CLI.
Nie musi od razu uzywac AI.

### 5. Model Layer

Modele sa wymienne.

System powinien umiec pracowac z:

- modelem cloud,
- modelem lokalnym,
- trybem offline bez modelu,
- regułami deterministycznymi tam, gdzie chodzi o finanse i obliczenia.

Zasada:

Obliczenia, flow platnosci i decyzje biznesowe nie moga zalezec od losowego outputu modelu.

### 6. Local Storage

Minimalny kierunek:

- orders lokalnie w filesystem lub SQLite,
- raporty lokalnie,
- kopie robocze PDF,
- historia sesji,
- eksporty dokumentow.

Docelowo:

- SQLite jako lokalna baza operacyjna,
- Supabase/PostgreSQL jako warstwa produkcyjna,
- storage PDF niezalezny od Render Free.

### 7. Operator GUI

GUI nie powinno byc pierwszym krokiem.
Najpierw runtime i pamiec.

Docelowe GUI:

- status systemu,
- ostatnie ordery,
- generowanie preview PDF,
- checklisty deploymentu,
- lokalna baza wiedzy,
- panel sesji i decyzji.

## Priorytety wdrozenia

### Faza 0 - stabilizacja dokumentu

Cel:

- utrzymac jeden aktualny opis systemu,
- zapisac architekture lokalnej warstwy,
- nie ruszac produkcji.

Status:

- ten dokument jest pierwszym artefaktem Fazy 0.

### Faza 1 - lokalny runbook operatora

Utworzyc instrukcje:

- jak uruchomic lokalny backend,
- jak wygenerowac testowy PDF,
- jak przetestowac order flow,
- jak sprawdzic diff,
- jak przygotowac deployment bez pushowania przypadkowych plikow.

### Faza 2 - lokalny audit command

Dodac prosty skrypt diagnostyczny, ktory sprawdza:

- status git,
- aktywne zmiany,
- obecne PDF/order files,
- czy `ADMIN_KEY` jest ustawiony dla testu,
- czy backend startuje lokalnie,
- czy `calculate_energy_case` nie zwraca `cost_after_pv = 0`.

### Faza 3 - pamiec decyzji

Wprowadzic katalog:

```text
docs/decisions/
```

Kazda wazna decyzja ma miec:

- date,
- problem,
- decyzje,
- czego nie ruszac,
- rollback plan.

### Faza 4 - lokalna baza operacyjna

Dodac SQLite jako lokalna pamiec pracy operatora.
Nie zastapi to od razu storage produkcyjnego.

Minimalne tabele:

- sessions,
- decisions,
- audits,
- generated_reports,
- local_tasks.

### Faza 5 - GUI operatora

Dopiero po stabilnym runtime:

- prosty dashboard lokalny,
- status KODEKS,
- przyciski do testow,
- lista runbookow,
- szybkie generowanie preview.

## Granice bezpieczenstwa

Nie ruszac bez osobnej decyzji:

- DNS,
- Render,
- Cloudflare,
- SMTP,
- platnosci,
- endpointow publicznych,
- flow admina,
- engine PDF,
- produkcyjnych ENV/secrets.

## Zasada cloud optional

Cloud ma byc rozszerzeniem, nie fundamentem.

System powinien dzialac w trybie:

```text
offline-first
local-first
cloud-assisted
```

## Najblizszy konkretny krok

Utworzyc lokalny runbook:

```text
docs/runbooks/local-operator-flow.md
```

Powinien zawierac:

- start backendu lokalnie,
- test formularza,
- test admin orders,
- test generowania PDF,
- test calculate_energy_case,
- test braku `cost_after_pv = 0`,
- checklist przed deployem.

## Wniosek

System Zablotny Online nie jest nowa funkcja KODEKS.
To warstwa operacyjna, ktora ma chronic pamiec, proces, jakosc i niezaleznosc pracy.

KODEKS pozostaje produktem.
System Zablotny Online staje sie warsztatem operatora.
