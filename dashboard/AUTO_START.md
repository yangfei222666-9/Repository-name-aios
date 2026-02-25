# AIOS Dashboard 开机自启

## 已配置
✅ 开机自启快捷方式已创建
- 位置：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AIOS Dashboard.lnk`
- 目标：`C:\Users\A\.openclaw\workspace\aios\dashboard\start_dashboard.bat`
- 窗口：最小化（后台运行）

## 手动控制

### 启动 Dashboard
双击运行：
```
C:\Users\A\.openclaw\workspace\aios\dashboard\start_dashboard.bat
```

### 停止 Dashboard
双击运行：
```
C:\Users\A\.openclaw\workspace\aios\dashboard\stop_dashboard.bat
```

### 访问界面
浏览器打开：http://localhost:9091

## 验证

重启电脑后：
1. 等待 10 秒
2. 打开浏览器访问 http://localhost:9091
3. 应该能看到 Dashboard 界面

## 取消自启

删除快捷方式：
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\AIOS Dashboard.lnk
```

或者运行：
```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\AIOS Dashboard.lnk"
```

## 故障排查

如果开机后 Dashboard 没启动：
1. 手动运行 `start_dashboard.bat` 看是否有错误
2. 检查 Python 路径是否正确（`C:\Program Files\Python312\python.exe`）
3. 检查端口 9091 是否被占用（`netstat -ano | findstr :9091`）
