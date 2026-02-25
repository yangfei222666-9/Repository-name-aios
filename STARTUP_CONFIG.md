# AIOS 开机自启动配置

## Windows 任务计划程序

### 方式 1：手动创建任务

1. 打开"任务计划程序"（taskschd.msc）
2. 创建基本任务
   - 名称：AIOS Warmup
   - 描述：AIOS 组件预热服务
3. 触发器：
   - 开始任务：当计算机启动时
   - 延迟任务时间：30 秒
4. 操作：
   - 程序/脚本：`C:\Program Files\Python312\python.exe`
   - 添加参数：`-X utf8 C:\Users\A\.openclaw\workspace\aios\warmup.py`
   - 起始于：`C:\Users\A\.openclaw\workspace\aios`
5. 条件：
   - ✅ 只有在计算机使用交流电源时才启动任务
   - ❌ 如果计算机改用电池电源，则停止
6. 设置：
   - ✅ 允许按需运行任务
   - ❌ 如果任务失败，每隔 1 分钟重新启动

### 方式 2：使用 PowerShell 脚本

运行以下命令创建任务：

```powershell
$action = New-ScheduledTaskAction -Execute "C:\Program Files\Python312\python.exe" -Argument "-X utf8 C:\Users\A\.openclaw\workspace\aios\warmup.py" -WorkingDirectory "C:\Users\A\.openclaw\workspace\aios"

$trigger = New-ScheduledTaskTrigger -AtStartup -RandomDelay (New-TimeSpan -Seconds 30)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "AIOS Warmup" -Action $action -Trigger $trigger -Settings $settings -Description "AIOS 组件预热服务" -RunLevel Highest
```

### 方式 3：使用启动文件夹

1. 创建快捷方式：
   - 目标：`C:\Program Files\Python312\python.exe -X utf8 C:\Users\A\.openclaw\workspace\aios\warmup.py`
   - 起始位置：`C:\Users\A\.openclaw\workspace\aios`
2. 复制到启动文件夹：
   - `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

---

## Linux systemd

### 创建服务文件

```bash
sudo nano /etc/systemd/system/aios-warmup.service
```

内容：

```ini
[Unit]
Description=AIOS Warmup Service
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/aios
ExecStart=/usr/bin/python3 /path/to/aios/warmup.py
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### 启用服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable aios-warmup.service
sudo systemctl start aios-warmup.service
sudo systemctl status aios-warmup.service
```

---

## macOS launchd

### 创建 plist 文件

```bash
nano ~/Library/LaunchAgents/com.aios.warmup.plist
```

内容：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aios.warmup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/path/to/aios/warmup.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/aios</string>
</dict>
</plist>
```

### 加载服务

```bash
launchctl load ~/Library/LaunchAgents/com.aios.warmup.plist
launchctl start com.aios.warmup
```

---

## 验证

### 检查任务状态（Windows）

```powershell
Get-ScheduledTask -TaskName "AIOS Warmup"
Get-ScheduledTaskInfo -TaskName "AIOS Warmup"
```

### 手动运行测试

```powershell
Start-ScheduledTask -TaskName "AIOS Warmup"
```

### 查看日志

检查 AIOS 日志文件：
- `C:\Users\A\.openclaw\workspace\aios\data\performance_stats.jsonl`
- `C:\Users\A\.openclaw\workspace\aios\data\events.jsonl`

---

## 故障排查

### 任务未运行

1. 检查任务计划程序历史记录
2. 确认 Python 路径正确
3. 确认脚本路径正确
4. 检查权限设置

### 预热失败

1. 手动运行 `warmup.py` 查看错误
2. 检查依赖是否安装
3. 检查文件权限

### 性能问题

1. 运行 `test_warmup.py` 验证性能
2. 检查系统资源占用
3. 查看性能监控数据

---

*配置时间：2026-02-24*  
*版本：v1.0*
