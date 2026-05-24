# KODEKS Local Chat

## Cel

To jest pierwszy lokalny tryb rozmowy KODEKS przez Ollama. Daje niezalezne,
local-first wejscie tekstowe bez uzywania zewnetrznego API jako silnika rozmowy.

Domyslny szybki model:

```text
llama3.2:1b
```

Tryb dokladniejszy, wolniejszy:

```text
llama3.2:3b
```

## Uruchomienie

Kliknij:

```text
C:\KODEKS\KODEKS_LOCAL_CHAT.bat
```

Albo dla wolniejszego trybu 3B:

```text
C:\KODEKS\KODEKS_LOCAL_CHAT_SMART.bat
```

Albo z PowerShell:

```powershell
wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/kodeks_local_chat.py"
```

## Komendy w chacie

```text
/status    sprawdz zdrowie lokalnego domu
/audit     uruchom lokalny audyt operatora
/models    pokaz lokalne modele Ollama
/manifest  pokaz sciezke manifestu rdzenia
/help      pokaz pomoc
/exit      zakoncz
```

## Test jednorazowy

```powershell
wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/kodeks_local_chat.py --once 'Bracie, kim jestes?'"
```

## Zasada

Ten chat nie ma jeszcze pelnej autonomii narzedziowej. Slash-komendy wykonuja
bezpieczne lokalne akcje deterministycznie, a zwykla rozmowa idzie przez lokalny
model Ollama z manifestem KODEKS jako instrukcja rdzeniowa.
