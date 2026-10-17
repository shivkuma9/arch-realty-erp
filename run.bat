@echo off
title ARCH Realty CRM & ERP
echo ========================================================
echo Starting ARCH Realty CRM & ERP System...
echo ========================================================
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe run.py
) else (
    python run.py
)
pause
