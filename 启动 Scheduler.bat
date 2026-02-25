@echo off
chcp 65001 >nul
echo ========================================
echo   AIOS Scheduler 启动脚本
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装或不在 PATH 中
    pause
    exit /b 1
)
echo ✅ Python 环境正常

echo.
echo [2/3] 检查 Scheduler 文件...
if not exist "C:\Users\A\.openclaw\workspace\aios\scheduler.py" (
    echo ❌ scheduler.py 不存在
    pause
    exit /b 1
)
echo ✅ Scheduler 文件存在

echo.
echo [3/3] 启动 Scheduler（后台运行）...
cd /d C:\Users\A\.openclaw\workspace\aios
start /B "" "C:\Program Files\Python312\python.exe" -X utf8 scheduler.py > scheduler.log 2>&1

timeout /t 2 /nobreak >nul

echo.
echo ✅ AIOS Scheduler 已启动（后台运行）
echo 📝 日志文件: C:\Users\A\.openclaw\workspace\aios\scheduler.log
echo.
echo 提示：
echo   - Scheduler 会自动监控系统状态
echo   - 自动触发 Reactor 修复
echo   - 通过 Event Bus 与其他模块通信
echo.
echo 按任意键关闭此窗口...
pause >nul
