@echo off
setlocal
title TDK KODEKS LOCAL HOUSE

echo ================================================
echo   TDK ^& ProService / KODEKS - LOCAL HOUSE
echo ================================================
echo.
echo Startuje lokalny dom:
echo - KODEKS API
echo - TDK backend
echo - TDK frontend
echo - monitoring
echo.

wsl.exe bash -lc "cd /mnt/c/KODEKS && bash scripts/start_local_house_wsl.sh"

echo.
echo Otwieram lokalne panele...
start "" "http://127.0.0.1:8001"
start "" "http://127.0.0.1:8001/admin/orders?admin_key=test-admin"
start "" "http://127.0.0.1:5174"
start "" "http://127.0.0.1:3000"

echo.
echo Gotowe. Jesli monitoring pokazal PASS, lokalny dom dziala.
echo.
pause
