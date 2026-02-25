@echo off
REM Stop AIOS Dashboard

echo Stopping Dashboard...

REM Find and kill python.exe running server.py
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%a" get CommandLine 2>nul | findstr /C:"dashboard" >nul
    if not errorlevel 1 (
        taskkill /F /PID %%a >nul 2>&1
        echo Dashboard stopped (PID %%a)
    )
)

echo Done
timeout /t 2 /nobreak >nul
