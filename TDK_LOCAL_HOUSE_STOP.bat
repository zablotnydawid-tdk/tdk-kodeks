@echo off
setlocal
title TDK KODEKS LOCAL HOUSE STOP

echo ================================================
echo   TDK ^& ProService / KODEKS - STOP
echo ================================================
echo.

wsl.exe bash -lc "cd /mnt/c/KODEKS && bash scripts/stop_local_house_wsl.sh"

echo.
echo Gotowe.
pause
