@echo off
REM ===============================================
REM   ARCH Realty ERP/CRM - One-Click Launcher
REM   Double-click this file to start the server
REM ===============================================

cd /d "%~dp0"

echo.
echo ==========================================================
echo        ARCH Realty ERP/CRM - Ahmedabad Enterprise
echo ==========================================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found in .\venv
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Set Flask environment variables
set FLASK_APP=run.py
set FLASK_ENV=development

REM Initialize database and demo data if not present
if not exist "instance\arch_realty.db" (
    echo [INFO] First time launch detected. Initializing database and demo data...
    python scripts\seed_demo_data.py
    echo [OK] Database and demo datasets seeded successfully.
)

echo.
echo ==========================================================
echo   LOGIN CREDENTIALS (Password for all: admin123):
echo   - Super Admin:       admin
echo   - Director:          director
echo   - Sales Manager:     manager
echo   - Senior Sales Exec: sales_rahul
echo   - Field Executive:   field_amit
echo   - Accounts Officer:  accounts_neha
echo   - HR Operations:     hr_anita
echo ==========================================================
echo.
echo [INFO] Starting web application server...
echo [INFO] Open your web browser at: http://127.0.0.1:5000
echo [INFO] Press Ctrl+C in this window to stop the server.
echo.

python -m flask run --host=127.0.0.1 --port=5000

pause
