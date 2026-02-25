# AIOS 工作流管理

## 概述

AIOS 工作流系统允许你自动化执行一系列任务，支持定时调度、条件判断和通知。

## 内置工作流

系统已预装 5 个工作流：

### 1. 每日健康检查 (wf-001-daily-health-check)
- **调度**: 每天早上 9:00
- **功能**: 
  - 运行 Pipeline 检查系统状态
  - 检查 Evolution Score，低于 0.3 时告警
  - 生成每日报告

### 2. 自动备份 (wf-002-auto-backup)
- **调度**: 每天凌晨 2:00
- **功能**:
  - 备份 AIOS 数据
  - 备份 Memory 文件
  - 清理 7 天前的旧备份

### 3. 错误告警 (wf-003-error-alert)
- **调度**: 每 5 分钟
- **功能**:
  - 检查最近 1 小时错误数
  - 超过 10 个错误时告警
  - 自动触发 Reactor 修复

### 4. 周报生成 (wf-004-weekly-report)
- **调度**: 每周一早上 9:00
- **功能**:
  - 生成周趋势报告
  - 检查记忆盲区
  - 发送周报通知

### 5. Agent 清理 (wf-005-agent-cleanup)
- **调度**: 每天凌晨 0:00
- **功能**:
  - 清理闲置的 Agent
  - 统计 Agent 使用情况

## 使用方法

### 列出所有工作流
```powershell
cd C:\Users\A\.openclaw\workspace\aios
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py list
```

### 执行工作流
```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py execute wf-001-daily-health-check
```

### 启用/禁用工作流
```powershell
# 禁用
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py disable wf-002-auto-backup

# 启用
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py enable wf-002-auto-backup
```

### 导入工作流
```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py import custom_workflows.json
```

### 导出工作流
```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py export wf-001-daily-health-check my_workflow.json
```

## 工作流格式

```json
{
  "workflows": [
    {
      "id": "wf-custom-001",
      "name": "自定义工作流",
      "description": "工作流描述",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "cron": "0 9 * * *",
        "timezone": "Asia/Shanghai"
      },
      "steps": [
        {
          "name": "步骤名称",
          "type": "command",
          "command": "python script.py"
        },
        {
          "name": "条件检查",
          "type": "check",
          "condition": "error_count > 10",
          "action": "notify",
          "message": "告警消息"
        },
        {
          "name": "发送通知",
          "type": "notify",
          "message": "通知内容"
        }
      ]
    }
  ]
}
```

## 步骤类型

### 1. command - 执行命令
```json
{
  "name": "运行脚本",
  "type": "command",
  "command": "python script.py"
}
```

### 2. check - 条件检查
```json
{
  "name": "检查错误率",
  "type": "check",
  "condition": "error_count > 10",
  "action": "notify",
  "message": "错误数过多"
}
```

### 3. notify - 发送通知
```json
{
  "name": "发送通知",
  "type": "notify",
  "message": "任务完成"
}
```

## 调度类型

### Cron 表达式
```json
{
  "type": "cron",
  "cron": "0 9 * * *",
  "timezone": "Asia/Shanghai"
}
```

常用 Cron 表达式：
- `0 9 * * *` - 每天 9:00
- `0 */6 * * *` - 每 6 小时
- `0 9 * * 1` - 每周一 9:00
- `0 0 1 * *` - 每月 1 号 0:00

### 间隔执行
```json
{
  "type": "interval",
  "interval_minutes": 5
}
```

## 集成到 HEARTBEAT

将工作流调度器添加到 HEARTBEAT.md：

```markdown
### 每次心跳：工作流调度
- 运行 `python -X utf8 workflow_manager.py check_schedule`
- 检查是否有到期的工作流
- 自动执行到期的工作流
- 静默执行，除非有失败
```

## 最佳实践

1. **命名规范**: 使用 `wf-XXX-descriptive-name` 格式
2. **描述清晰**: 写明工作流的目的和功能
3. **步骤简洁**: 每个步骤只做一件事
4. **错误处理**: 关键步骤添加条件检查
5. **通知适度**: 只在重要事件时发送通知

## 故障排查

### 工作流执行失败
1. 检查命令路径是否正确
2. 检查 Python 环境是否正确
3. 查看错误日志

### 调度不生效
1. 确认工作流已启用
2. 检查 Cron 表达式是否正确
3. 确认时区设置

## 示例：创建自定义工作流

```json
{
  "workflows": [
    {
      "id": "wf-custom-lol-update",
      "name": "LOL 数据更新",
      "description": "每周检查 LOL 版本并更新数据",
      "enabled": true,
      "schedule": {
        "type": "cron",
        "cron": "0 10 * * 1",
        "timezone": "Asia/Shanghai"
      },
      "steps": [
        {
          "name": "检查版本",
          "type": "command",
          "command": "python C:\\Users\\A\\Desktop\\ARAM-Helper\\check_version.py"
        },
        {
          "name": "更新数据",
          "type": "command",
          "command": "python C:\\Users\\A\\Desktop\\ARAM-Helper\\fetch_real_data.py"
        },
        {
          "name": "发送通知",
          "type": "notify",
          "message": "✅ LOL 数据已更新"
        }
      ]
    }
  ]
}
```

保存为 `lol_workflow.json`，然后导入：

```powershell
& "C:\Program Files\Python312\python.exe" -X utf8 workflow_manager.py import lol_workflow.json
```
