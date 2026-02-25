@echo off
chcp 65001 >nul
echo ========================================
echo   AIOS Scheduler 停止脚本
echo ========================================
echo.

echo 正在查找 Scheduler 进程...

for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO LIST ^| findstr /C:"PID:"') do (
    wmic process where "ProcessId=%%i" get CommandLine 2>nul | findstr /C:"scheduler.py" >nul
    if !errorlevel! equ 0 (
        echo 找到 Scheduler 进程: PID %%i
        taskkill /PID %%i /F >nul 2>&1
        echo ✅ Scheduler 已停止
        goto :done
    )
)

echo ⚠️ 未找到运行中的 Scheduler 进程

:done
echo.
pause
