@echo off
rem Build a standalone GRAP-SQL.exe (no Python install needed to run it).
rem Requires PyInstaller:  python -m pip install pyinstaller

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo Rendering the app icon...
python tools\make_icon.py

echo Building the executable (this can take a minute)...
python -m PyInstaller --noconfirm --clean GRAP-SQL.spec

if errorlevel 1 (
    echo.
    echo Build failed. Make sure PyInstaller is installed:
    echo     python -m pip install pyinstaller
    pause
    exit /b 1
)

echo.
echo Done! Your app is in  dist\GRAP-SQL\GRAP-SQL.exe
pause
