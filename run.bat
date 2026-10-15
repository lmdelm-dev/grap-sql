@echo off
rem GRAP-SQL - just double-click me.
rem Looks for a Python that has PySide6 installed, then starts the app.

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo.
    echo I can't find Python on this computer.
    echo Install it from https://www.python.org/downloads/  - tick "Add python.exe to PATH".
    echo Then run "pip install -r requirements.txt" once, and double-click me again.
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
python -c "import PySide6" >nul 2>nul
if errorlevel 1 (
    echo.
    echo PySide6 (the graphics library) is missing. Installing it now...
    python -m pip install -r requirements.txt
)

python -m sqlschool
if errorlevel 1 pause