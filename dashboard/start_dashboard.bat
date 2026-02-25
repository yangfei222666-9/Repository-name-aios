@echo off
REM AIOS Dashboard Auto-Start Script
REM Run this at startup to launch Dashboard in background

cd /d C:\Users\A\.openclaw\workspace\aios\dashboard

REM Check if already running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq AIOS Dashboard*" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Dashboard already running
    exit /b 0
)

REM Start Dashboard in background (hidden window)
start /B "" "C:\Program Files\Python312\python.exe" server.py

echo Dashboard started
timeout /t 3 /nobreak >nul
