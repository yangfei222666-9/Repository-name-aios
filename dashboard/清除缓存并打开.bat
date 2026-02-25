@echo off
echo 正在关闭所有浏览器...
taskkill /F /IM msedge.exe 2>nul
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM firefox.exe 2>nul

echo 等待 2 秒...
timeout /t 2 /nobreak >nul

echo 清除 Edge 缓存...
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" 2>nul
rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Code Cache" 2>nul

echo 重新打开 Dashboard...
start http://localhost:9091

echo 完成！请等待浏览器打开。
pause
