@echo off
rem Run the test suite headless (no window appears). Just double-click me.

cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set QT_QPA_PLATFORM=offscreen
set "BT=%TEMP%\sqlschool-tests-%RANDOM%"
python -m pytest tests -p no:cacheprovider --basetemp="%BT%"
if errorlevel 1 pause