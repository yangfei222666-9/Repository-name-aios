# AIOS - AI Operating System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.6-orange.svg)](https://github.com/yangfei222666-9/aios)

**从监控 → 自动修复 → 自我进化**

AIOS 是一个轻量级的 AI 操作系统框架，提供完整的事件驱动、自动修复和自我进化能力。

---

## 🚀 10秒快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/yangfei222666-9/aios.git
cd aios

# 2. 运行演示
python aios.py demo

# 3. 查看系统状态
python aios.py status
```

**零依赖，只需要 Python 3.8+**

---

## ✨ 核心功能

### EventBus（事件总线）
系统心脏，所有事件通过这里流转。支持发布/订阅模式，自动持久化到 EventStore。

```python
from core.event_bus import get_event_bus
from core.event import create_event, EventType

bus = get_event_bus()
event = create_event(EventType.RESOURCE_HIGH, {"resource": "cpu", "value": 85})
bus.emit(event)
```

### Scheduler（任务调度）
优先级队列调度系统，支持 P0/P1/P2 三级优先级，最多 5 个并行任务，自动超时重试。

```python
from core.scheduler_v2 import SchedulerV2, Task, Priority

scheduler = SchedulerV2()
scheduler.start()
scheduler.submit(Task(name="fix_cpu", priority=Priority.P0, handler=my_handler))
```

### Reactor（自动修复）
基于 Playbook 的自动修复引擎，匹配事件模式并执行修复动作。

```python
from core.production_reactor import ProductionReactor

reactor = ProductionReactor()
reactor.load_playbooks("playbooks/")
reactor.handle_event(event)  # 自动匹配并执行 playbook
```

### ScoreEngine（评分引擎）
实时计算系统健康度，追踪任务成功率、修复率、运行时间等指标。

```python
from core.score_engine import ScoreEngine

engine = ScoreEngine()
score = engine.get_score()  # 0.0 - 1.0
print(f"Evolution Score: {score:.2f}")
```

### Agent System（Agent 管理）
自动调度和管理 AI Agent，支持健康检查、自动恢复、性能追踪。

```python
from agent_system.auto_dispatcher import AutoDispatcher

dispatcher = AutoDispatcher()
dispatcher.start()
dispatcher.dispatch_task({"type": "worker", "params": {...}})
```

### Dashboard（实时监控）
Web 界面展示系统状态、任务时间线、进化曲线。

```bash
python aios.py dashboard
# 访问 http://localhost:9091
```

---

## 🎯 使用场景

### 场景 1: 文件监控 + 自动备份（推荐）

自动监控重要文件，检测到变化立即备份。

```bash
python demo_file_monitor.py
```

**效果：**
- 🔍 每 2 秒检查文件变化（哈希对比）
- 🚨 检测到修改立即触发备份
- 💾 自动备份到 backups/ 目录（带时间戳）
- ✅ 验证备份完整性（哈希匹配）
- 📊 记录所有事件和指标

**输出示例：**
```
[19:35:38] ✅ 检查 #1: 文件未变化
[19:35:42] 🚨 检测到文件变化！
💾 触发 AIOS 自动备份...
   ✅ 备份成功: important_config_20260225_193542.json
   ✅ 备份验证通过（哈希匹配）
[19:35:44] ✅ 检查 #4: 文件未变化
```

**真实用途：**
- 配置文件自动备份（nginx.conf、config.json）
- 代码文件版本追踪（自动保存历史版本）
- 重要文档保护（防止误删除或误修改）

### 场景 2: API 健康检查

自动监控 API 服务，连续失败时自动修复。

```bash
python demo_api_health.py
```

**效果：**
- 🔍 每 2 秒检查 API 健康状态
- 🚨 连续失败 2 次触发告警
- 🔧 自动重启服务
- ✅ 验证修复效果
- 📊 记录所有事件和指标

**输出示例：**
```
[16:54:23] ✅ 检查 #1: 健康
[16:54:27] ❌ 检查 #4: 故障
[16:54:29] ❌ 检查 #5: 故障
🚨 检测到连续故障，触发 AIOS 自动修复...
✅ 自动修复成功！
[16:54:34] ✅ 检查 #6: 健康（已恢复）
```

### 场景 3: 资源监控与自动修复

监控 CPU/内存使用率，超过阈值时自动清理。

```python
from core.event_bus import get_event_bus
from core.event import create_event, EventType

bus = get_event_bus()

# 模拟高 CPU 事件
event = create_event(EventType.RESOURCE_HIGH, {
    "resource": "cpu",
    "value": 85,
    "threshold": 80
})
bus.emit(event)

# Reactor 自动匹配 playbook 并执行修复
```

### 场景 4: Agent 任务调度

自动分配任务给健康的 Agent，失败时自动重试。

```python
from agent_system.auto_dispatcher import AutoDispatcher

dispatcher = AutoDispatcher()
dispatcher.start()

# 提交任务
task = {
    "type": "worker",
    "params": {"file": "data.csv"}
}
result = dispatcher.dispatch_task(task)
```

---

## 📖 API 参考

### 核心类

| 类名 | 功能 | 主要方法 |
|------|------|----------|
| `EventBus` | 事件总线 | `emit(event)`, `subscribe(pattern, callback)` |
| `SchedulerV2` | 任务调度 | `submit(task)`, `start()`, `stop()` |
| `ProductionReactor` | 自动修复 | `load_playbooks(dir)`, `handle_event(event)` |
| `ScoreEngine` | 评分引擎 | `get_score()`, `get_breakdown()` |
| `AutoDispatcher` | Agent 调度 | `dispatch_task(task)`, `check_agent_health()` |

### 事件类型

| 事件类型 | 说明 | 数据字段 |
|----------|------|----------|
| `RESOURCE_HIGH` | 资源使用率高 | `resource`, `value`, `threshold` |
| `TASK_FAILED` | 任务失败 | `task_id`, `error_message` |
| `AGENT_ERROR` | Agent 错误 | `agent_id`, `error_type` |
| `PIPELINE_COMPLETE` | Pipeline 完成 | `pipeline_id`, `duration` |

### 优先级

| 优先级 | 说明 | 使用场景 |
|--------|------|----------|
| `P0` | 紧急 | 系统崩溃、资源临界 |
| `P1` | 高 | Agent 错误、任务失败 |
| `P2` | 普通 | 日志记录、Pipeline 完成 |

---

## ⚙️ 配置说明

### 环境变量

```bash
# Windows
set AIOS_LOG_PATH=aios/logs/aios.jsonl
set AIOS_EVENTS_PATH=events.jsonl
set AIOS_DASHBOARD_PORT=9091

# Linux/Mac
export AIOS_LOG_PATH="aios/logs/aios.jsonl"
export AIOS_EVENTS_PATH="events.jsonl"
export AIOS_DASHBOARD_PORT=9091
```

### Playbook 配置

创建 `playbooks/my_playbook.json`：

```json
{
  "id": "cpu_high_kill_idle",
  "description": "CPU 高时杀掉空闲 Agent",
  "trigger": {
    "event_type": "resource.high",
    "conditions": {
      "resource": "cpu",
      "value": {"$gt": 80}
    }
  },
  "actions": [
    {
      "type": "kill_idle_agents",
      "params": {"max_count": 3}
    }
  ],
  "validation": {
    "check": "cpu_below_threshold",
    "timeout_seconds": 30
  },
  "risk_level": "low"
}
```

---

## 🧪 测试

```bash
# 运行所有测试
python aios.py test

# 运行性能基准测试
python aios.py benchmark

# 运行心跳检查
python aios.py heartbeat
```

---

## ❓ FAQ

### Q: 需要安装依赖吗？
A: **不需要！** AIOS 核心是零依赖的，只需要 Python 3.8+。Dashboard 需要安装 `flask`（可选）。

### Q: 支持哪些 Python 版本？
A: Python 3.8, 3.9, 3.10, 3.11, 3.12 都支持。

### Q: 可以在生产环境使用吗？
A: 可以！AIOS v0.6 已经过充分测试，性能优异。建议先在测试环境验证。

### Q: 如何集成到我的项目？
A: 只需要导入核心模块：
```python
from core.event_bus import get_event_bus
from core.event import create_event, EventType
```

### Q: EventStore 存储在哪里？
A: 默认存储在 `data/events/` 目录，按日期分片（`events_YYYY-MM-DD.jsonl`）。

### Q: 如何自定义 Playbook？
A: 在 `playbooks/` 目录创建 JSON 文件，参考"配置说明"部分的示例。

### Q: Dashboard 无法访问？
A: 检查端口是否被占用，或使用 `python aios.py dashboard --port 8080` 指定其他端口。

---

## 📄 License

MIT License - 详见 [LICENSE](LICENSE)

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📚 更多资源

- **GitHub**: https://github.com/yangfei222666-9/aios
- **文档**: 查看 `docs/` 目录
- **示例**: 查看 `demo/` 目录

---

**AIOS v0.6** - 让 AI 系统自己运行、自己看、自己进化！🚀
