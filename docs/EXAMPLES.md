# AIOS 使用示例

## 快速开始

### 1. 启动 Dashboard

```bash
cd C:\Users\A\.openclaw\workspace\aios\dashboard
python server.py
```

访问 http://127.0.0.1:9091 查看实时监控。

### 2. 手动触发 Orchestrator

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python orchestrator.py
```

输出：
```
==================================================
开始 Agent 闭环周期
==================================================
=== Monitor Agent ===
  发现 1 个告警
=== Analyst Agent ===
  分析完成
=== Optimizer Agent ===
  生成了 1 个优化行动
=== Executor Agent ===
  执行: 增加低成功率 Playbook 的超时时间
  执行了 1 个行动
=== Validator Agent ===
  验证完成
=== Learner Agent ===
  学习完成

=== 周期完成 ===
ORCHESTRATOR_OK
```

### 3. 查看 Evolution Score

```bash
cd C:\Users\A\.openclaw\workspace\aios\learning
python baseline.py snapshot
```

输出：
```json
{
  "ts": "2026-02-24T12:47:18",
  "evolution_score": 0.52,
  "tool_success_rate": 0.95,
  "grade": "healthy"
}
```

## 常见场景

### 场景 1：CPU 使用率过高

**问题：** CPU 使用率持续 >80%

**自动修复流程：**

1. **Monitor 检测异常**
```bash
python aios/agent_system/monitor_agent.py
```

输出：
```
MONITOR_ALERT:1
- CPU 使用率: 85% (阈值: 80%)
```

2. **Scheduler 决策**
```
事件: resource.high (cpu=85%)
优先级: high
决策: 触发 Reactor
```

3. **Reactor 执行**
```bash
python aios/core/reactor.py
```

匹配 Playbook: `reduce_heartbeat_freq`
```json
{
  "id": "reduce_heartbeat_freq",
  "actions": [
    {"type": "config.update", "path": "heartbeat.interval", "value": 120}
  ],
  "risk": "low",
  "auto_execute": true
}
```

4. **验证结果**
```
等待 5 分钟...
CPU 使用率: 65% ✅
验证通过
```

5. **更新评分**
```
evolution_score: 0.45 → 0.52
```

### 场景 2：工具调用失败率高

**问题：** 最近 1 小时工具成功率 <80%

**手动干预：**

1. **查看失败日志**
```bash
cd C:\Users\A\.openclaw\workspace\aios\data
tail -n 100 events.jsonl | grep "error"
```

2. **分析失败模式**
```bash
python aios/learning/knowledge_extractor.py
```

输出：
```
发现重复错误模式:
- exec timeout (出现 5 次)
- web_fetch connection error (出现 3 次)
```

3. **应用修复**
```bash
# 增加超时时间
python aios/core/reactor.py --playbook increase_timeout
```

4. **验证效果**
```bash
python aios/learning/baseline.py snapshot
```

### 场景 3：Agent 创建失败

**问题：** Agent Spawn 超时或失败

**排查步骤：**

1. **检查熔断器状态**
```bash
cat aios/agent_system/circuit_breaker_state.json
```

输出：
```json
{
  "coder_agent": {
    "state": "open",
    "failures": 3,
    "last_failure": "2026-02-24T12:30:00"
  }
}
```

2. **手动重置熔断器**
```bash
python aios/agent_system/reset_breaker.py --agent coder_agent
```

3. **重试创建**
```bash
python aios/agent_system/auto_dispatcher.py spawn --type coder --task "修复 bug"
```

### 场景 4：系统降级

**问题：** Evolution Score 降到 0.3 (degraded)

**诊断流程：**

1. **查看 Dashboard**
访问 http://127.0.0.1:9091，检查：
- 错误率是否上升
- 资源使用是否异常
- Agent 是否正常运行

2. **查看最近事件**
```bash
tail -n 50 aios/data/events.jsonl
```

3. **运行健康检查**
```bash
python aios/maintenance/health_check.py
```

输出：
```
系统健康检查报告:
- Evolution Score: 0.32 (degraded) ⚠️
- 事件日志大小: 2.3 MB (正常)
- Agent 状态: 5/9 活跃 (正常)
- 磁盘使用率: 45% (正常)

建议:
1. 检查最近 1 小时的错误日志
2. 重启降级的 Agent
3. 清理过期数据
```

4. **应用修复**
```bash
# 自动修复
python aios/maintenance/auto_fix.py

# 或手动修复
python aios/agent_system/restart_agent.py --agent monitor_agent
python aios/maintenance/auto_cleanup.py
```

## 高级用法

### 自定义 Playbook

创建新的 Playbook：

```json
{
  "id": "restart_slow_agent",
  "trigger": {
    "event_type": "agent.slow",
    "conditions": {
      "latency_ms": ">5000"
    }
  },
  "actions": [
    {
      "type": "agent.restart",
      "target": "{{agent_id}}"
    }
  ],
  "risk": "medium",
  "auto_execute": false,
  "verify": {
    "metric": "agent.latency_ms",
    "expected": "<3000"
  }
}
```

添加到 `aios/data/playbooks.json`，Reactor 会自动加载。

### 手动触发 Reactor

```bash
# 触发特定 Playbook
python aios/core/reactor.py --playbook reduce_heartbeat_freq

# 模拟事件触发
python aios/core/reactor.py --event resource.high --payload '{"resource":"cpu","value":85}'
```

### 导出监控数据

```bash
# 导出最近 7 天的 Evolution Score
python aios/learning/export_metrics.py --days 7 --output metrics.csv

# 导出事件日志
python aios/data/export_events.py --start "2026-02-20" --end "2026-02-24" --output events.json
```

### 批量管理 Agent

```bash
# 列出所有 Agent
python aios/agent_system/list_agents.py

# 归档闲置 Agent（>7天未活跃）
python aios/agent_system/archive_idle.py --days 7

# 批量重启 Agent
python aios/agent_system/restart_all.py --type coder
```

## 集成到 OpenClaw

### 心跳任务配置

编辑 `HEARTBEAT.md`：

```markdown
### 每小时：AIOS Agent 闭环
- 运行 orchestrator.py
- 完整 OODA 循环
- 上次执行时间记录在 memory/selflearn-state.json 的 last_orchestrator

### 每10分钟：Reactor 自动触发
- 监听最近 10 分钟的事件
- 自动匹配 playbooks 并执行修复
- 上次执行时间记录在 memory/selflearn-state.json 的 last_reactor
```

### Cron 定时任务

使用 OpenClaw 的 cron 功能：

```bash
# 每天 9:00 运行健康检查
openclaw cron add --schedule "0 9 * * *" --task "运行 AIOS 健康检查" --command "python aios/maintenance/health_check.py"

# 每周一 0:00 清理过期数据
openclaw cron add --schedule "0 0 * * 1" --task "清理 AIOS 过期数据" --command "python aios/maintenance/auto_cleanup.py"
```

## 监控最佳实践

### 1. 定期查看 Dashboard

每天至少查看一次 Dashboard，关注：
- Evolution Score 趋势（是否下降）
- 错误率（是否上升）
- Agent 状态（是否有降级）
- 心跳任务状态（是否有超时）

### 2. 设置告警阈值

编辑 `aios/core/alerts.py`：

```python
ALERT_THRESHOLDS = {
    "evolution_score": 0.5,  # 低于 0.5 告警
    "error_rate": 0.1,       # 错误率 >10% 告警
    "cpu_usage": 80,         # CPU >80% 告警
    "memory_usage": 85       # 内存 >85% 告警
}
```

### 3. 定期备份

```bash
# 手动备份
python aios/maintenance/backup.py

# 自动备份（每天）
# 已在 HEARTBEAT.md 中配置
```

### 4. 定期审查 Playbooks

每月审查一次 `aios/data/playbooks.json`：
- 删除无效的 Playbook
- 调整风险级别
- 优化触发条件

## 性能调优

### 降低心跳频率

如果系统资源紧张，可以降低心跳频率：

```markdown
# HEARTBEAT.md
### 每2小时：AIOS Agent 闭环
（原来是每小时）

### 每30分钟：Reactor 自动触发
（原来是每10分钟）
```

### 限制事件日志大小

```bash
# 自动清理 >7天的事件
python aios/maintenance/auto_cleanup.py --days 7

# 压缩旧日志
python aios/maintenance/compress_logs.py
```

### 优化 Agent 数量

```bash
# 归档闲置 Agent
python aios/agent_system/archive_idle.py --days 7

# 限制最大 Agent 数
# 编辑 aios/agent_system/config.py
MAX_AGENTS = 10
```

## 故障恢复

### 完全重置

如果系统出现严重问题，可以完全重置：

```bash
# 备份当前数据
python aios/maintenance/backup.py --output backup_$(date +%Y%m%d).tar.gz

# 清理所有数据
rm -rf aios/data/events.jsonl
rm -rf aios/data/baseline.jsonl
rm -rf aios/agent_system/data/agents.jsonl

# 重新初始化
python aios/init.py
```

### 从备份恢复

```bash
# 解压备份
tar -xzf backup_20260224.tar.gz -C aios/

# 验证数据完整性
python aios/maintenance/verify_data.py

# 重启服务
python aios/dashboard/server.py
```

## 常见问题

### Q: Dashboard 显示 "WebSocket 连接失败"
**A:** 检查服务是否运行，或使用 HTTP 降级模式（自动切换）。

### Q: Orchestrator 一直输出 "ORCHESTRATOR_SKIP"
**A:** 正常，说明未到执行时间（每小时一次）。

### Q: Reactor 不自动执行 Playbook
**A:** 检查 Playbook 的 `auto_execute` 是否为 `true`，以及风险级别是否为 `low`。

### Q: Evolution Score 一直是 0
**A:** 运行 `python aios/learning/baseline.py snapshot` 生成初始快照。

### Q: Agent 创建失败
**A:** 检查熔断器状态，可能需要手动重置。

## 下一步

- 阅读 [架构文档](ARCHITECTURE.md) 了解系统设计
- 查看 [API 文档](API.md) 了解接口定义
- 参与 [开发指南](CONTRIBUTING.md) 贡献代码

---

**版本：** v0.5  
**更新时间：** 2026-02-24  
**作者：** 珊瑚海 + 小九
