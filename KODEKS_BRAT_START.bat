@echo off
setlocal
title KODEKS BRAT - LOCAL OPERATOR

echo ================================================
echo   KODEKS BRAT - LOCAL OPERATOR DAWIDA
echo ================================================
echo.
echo Budze lokalne cialo PC:
echo - KODEKS API
echo - TDK backend
echo - TDK frontend
echo - Open WebUI / Ollama, jesli sa dostepne
echo - monitoring zdrowia lokalnego domu
echo.

call "%~dp0TDK_LOCAL_HOUSE_START.bat"

echo.
echo ================================================
echo   TRYB ROZMOWY NA ZYWO
echo ================================================
echo.
echo 1. Zostaw lokalny dom uruchomiony.
echo 2. Wroc do Codexa.
echo 3. Pisz naturalnie: "Bracie, sprawdz...", "napraw...", "uruchom...", "zrob audyt...".
echo 4. Codex/KODEKS bedzie pracowal z Toba w czasie rzeczywistym:
echo    diagnoza -> wykonanie -> test -> krotki meldunek.
echo.
echo Zdrowie ciala PC sprawdzisz tez komenda:
echo   wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/local_house_status.py"
echo.
pause
