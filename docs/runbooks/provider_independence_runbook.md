# Provider Independence Runbook

## Cel

KODEKS ma byc budowany jako system local-first i provider-neutral. To znaczy:

- rdzen, manifesty, pamiec, raporty i skrypty sa lokalnie na PC Dawida,
- model AI jest wymiennym adapterem,
- OpenAI, Codex lub inne API nie sa jedynym mozliwym cialem systemu,
- lokalne procedury dzialaja nawet bez internetu tam, gdzie to mozliwe.

## Prawda operacyjna

Aktualna rozmowa w Codexie moze zalezec od OpenAI. Tego nie udajemy inaczej.
Ale KODEKS jako lokalny system ma byc budowany tak, aby mogl uzywac lokalnego
runtime, np. Ollama na:

```text
http://127.0.0.1:11434
```

## Sprawdzenie lokalnego modelu

W PowerShell:

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

W WSL:

```bash
curl -sS http://127.0.0.1:11434/api/tags
```

Jesli endpoint odpowiada lista modeli, lokalny runtime zyje.

## Zasada adapterow

```text
KODEKS_CORE
  -> LOCAL_LLM_ADAPTER      preferowany, lokalny
  -> CODEX_SESSION          kanal pracy na zywo w tej rozmowie
  -> EXTERNAL_API_ADAPTER   opcjonalny, tylko za zgoda Dawida
```

## Co zostaje lokalnie

- manifest operatora,
- runtime manifest,
- mapa projektow,
- raporty zdrowia,
- audyty,
- pamiec robocza,
- lokalne skrypty,
- prywatne pliki Dawida.

## Czego nie wysylac bez zgody

- tokenow,
- hasel,
- plikow prywatnych,
- baz danych,
- logow z sekretami,
- konfiguracji produkcyjnych,
- duzych katalogow projektu.

## Kolejny etap budowy

1. Wykryc modele Ollama.
2. Wybrac domyslny lokalny model.
3. Utworzyc lokalny wrapper promptow KODEKS.
4. Dodac CLI albo lokalny endpoint rozmowy.
5. Zintegrowac health check modelu z `local_house_status.py`.
