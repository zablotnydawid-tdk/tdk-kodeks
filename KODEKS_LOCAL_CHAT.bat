@echo off
setlocal
title KODEKS LOCAL CHAT - OLLAMA

echo ================================================
echo   KODEKS LOCAL CHAT - LOCAL FIRST
echo ================================================
echo.
echo Uruchamiam lokalna rozmowe przez Ollama.
echo Domyslny model szybki: llama3.2:1b
echo.

wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/kodeks_local_chat.py --model llama3.2:1b"

echo.
pause
