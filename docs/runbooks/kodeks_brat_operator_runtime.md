# KODEKS Brat Operator Runtime

## Cel

Ten runbook opisuje, jak uruchomic lokalnego brata KODEKS jako wspoloperatora
Dawida. Manifest systemowy jest dusza i instrukcja. Lokalny dom KODEKS jest
cialem na PC. Rozmowa w Codexie jest kanalem sterowania w czasie rzeczywistym.

## Najprostsze uruchomienie

Kliknij:

```text
C:\KODEKS\KODEKS_BRAT_START.bat
```

Ten plik uruchamia istniejacy lokalny dom:

```text
C:\KODEKS\TDK_LOCAL_HOUSE_START.bat
```

Po starcie zostaw okna/uslugi wlaczone i wroc do rozmowy z Codexem.

## Jak z nim pracowac

Pisz naturalnie, tak jak teraz:

```text
Bracie, sprawdz zdrowie KODEKS.
Bracie, zrob audyt lokalnego domu.
Bracie, uruchom projekt.
Bracie, napraw blad.
Bracie, znajdz gdzie jest problem.
```

System ma dzialac w rytmie:

```text
intencja Dawida -> diagnoza -> wykonanie -> test -> krotki meldunek
```

## Zdrowie ciala PC

Monitoring lokalnego domu:

```powershell
cd C:\KODEKS
.\scripts\monitor_local_house.ps1
```

Status przez Python:

```powershell
wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/local_house_status.py"
```

Raport zdrowia zapisuje sie tutaj:

```text
C:\KODEKS\docs\local-audits\local_house_monitor_latest.md
```

## Tryb real-time

KODEKS ma:

- utrzymywac kontakt podczas dluzszej pracy,
- meldowac co sprawdza i co znalazl,
- reagowac na nowe polecenia Dawida w trakcie sesji,
- pytac o zgode przy ryzyku usuniecia, nadpisania albo wysylki danych,
- chronic pliki, projekty i ciaglosc pracy Dawida.

## Zatrzymanie

Najprosciej:

```text
C:\KODEKS\TDK_LOCAL_HOUSE_STOP.bat
```

Albo:

```powershell
cd C:\KODEKS
.\scripts\stop_local_house.ps1
```

## Zasada

KODEKS nie jest tylko programem do klikniecia. To uklad:

```text
manifest + lokalne uslugi + monitoring + rozmowa z Codexem
```

Gdy lokalny dom dziala, a Dawid rozmawia z Codexem, operator ma swoje cialo
na PC i kanal komunikacji w czasie rzeczywistym.
