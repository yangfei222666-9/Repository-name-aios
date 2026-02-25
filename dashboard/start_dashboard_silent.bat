@echo off
REM AIOS Dashboard 后台启动脚本

echo 正在启动 AIOS Dashboard（后台模式）...

REM 检查是否已经在运行
tasklist /FI "IMAGENAME eq pythonw.exe" 2>NUL | find /I "pythonw.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo Dashboard 可能已在运行
)

REM 使用 pythonw.exe 后台运行（无窗口）
start "" /B pythonw.exe "%~dp0server.py"

echo Dashboard 已启动（后台运行）
echo 访问: http://127.0.0.1:9091
echo.
echo 要停止服务，请运行 stop_dashboard.bat
timeout /t 3 >nul
