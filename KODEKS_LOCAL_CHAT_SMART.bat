@echo off
setlocal
title KODEKS LOCAL CHAT SMART - OLLAMA

echo ================================================
echo   KODEKS LOCAL CHAT SMART - LOCAL FIRST
echo ================================================
echo.
echo Uruchamiam lokalna rozmowe przez Ollama.
echo Model dokladniejszy, wolniejszy: llama3.2:3b
echo.

wsl.exe bash -lc "cd /mnt/c/KODEKS && .venv/bin/python scripts/kodeks_local_chat.py --model llama3.2:3b"

echo.
pause
