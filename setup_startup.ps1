# AIOS 自动配置开机自启动
# 需要管理员权限运行

Write-Host "=" * 60
Write-Host "AIOS 开机自启动配置"
Write-Host "=" * 60

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`n❌ 需要管理员权限！" -ForegroundColor Red
    Write-Host "请右键点击 PowerShell 并选择'以管理员身份运行'" -ForegroundColor Yellow
    exit 1
}

# 配置参数
$pythonPath = "C:\Program Files\Python312\python.exe"
$scriptPath = "C:\Users\A\.openclaw\workspace\aios\warmup.py"
$workingDir = "C:\Users\A\.openclaw\workspace\aios"
$taskName = "AIOS Warmup"

# 验证文件存在
Write-Host "`n1. 验证文件..."
if (-not (Test-Path $pythonPath)) {
    Write-Host "   ❌ Python 未找到: $pythonPath" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Python: $pythonPath" -ForegroundColor Green

if (-not (Test-Path $scriptPath)) {
    Write-Host "   ❌ 脚本未找到: $scriptPath" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ 脚本: $scriptPath" -ForegroundColor Green

# 删除旧任务（如果存在）
Write-Host "`n2. 检查现有任务..."
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "   ⚠️ 发现现有任务，正在删除..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "   ✅ 已删除旧任务" -ForegroundColor Green
}

# 创建新任务
Write-Host "`n3. 创建新任务..."

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "-X utf8 `"$scriptPath`"" `
    -WorkingDirectory $workingDir

$trigger = New-ScheduledTaskTrigger `
    -AtStartup `
    -RandomDelay (New-TimeSpan -Seconds 30)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5)

$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "AIOS 组件预热服务 - 系统启动时自动运行" `
        -ErrorAction Stop
    
    Write-Host "   ✅ 任务创建成功" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ 任务创建失败: $_" -ForegroundColor Red
    exit 1
}

# 验证任务
Write-Host "`n4. 验证任务..."
$task = Get-ScheduledTask -TaskName $taskName
if ($task) {
    Write-Host "   ✅ 任务已注册" -ForegroundColor Green
    Write-Host "   名称: $($task.TaskName)"
    Write-Host "   状态: $($task.State)"
    Write-Host "   触发器: 系统启动时（延迟 30 秒）"
}

# 测试运行
Write-Host "`n5. 测试运行..."
Write-Host "   正在启动任务..." -ForegroundColor Yellow

try {
    Start-ScheduledTask -TaskName $taskName
    Start-Sleep -Seconds 3
    
    $taskInfo = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "   ✅ 任务已执行" -ForegroundColor Green
    Write-Host "   上次运行: $($taskInfo.LastRunTime)"
    Write-Host "   上次结果: $($taskInfo.LastTaskResult)"
}
catch {
    Write-Host "   ⚠️ 测试运行失败: $_" -ForegroundColor Yellow
}

# 完成
Write-Host "`n" + "=" * 60
Write-Host "✅ 配置完成！" -ForegroundColor Green
Write-Host "=" * 60

Write-Host "`n下次系统启动时，AIOS 将自动预热组件。"
Write-Host "`n管理任务："
Write-Host "  查看状态: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "  手动运行: Start-ScheduledTask -TaskName '$taskName'"
Write-Host "  禁用任务: Disable-ScheduledTask -TaskName '$taskName'"
Write-Host "  删除任务: Unregister-ScheduledTask -TaskName '$taskName'"
Write-Host ""
