# AIOS v0.5 API文档

完整的API参考文档。

---

## 目录

- [EventBus API](#eventbus-api)
- [Event API](#event-api)
- [Scheduler API](#scheduler-api)
- [Reactor API](#reactor-api)
- [ScoreEngine API](#scoreengine-api)
- [AgentStateMachine API](#agentstatemachine-api)
- [Memory Palace API](#memory-palace-api)
- [自动化API](#自动化api)

---

## EventBus API

### `EventBus()`

创建事件总线实例。

```python
from aios.core.event_bus import EventBus

bus = EventBus()
```

### `subscribe(event_type: str, handler: Callable)`

订阅事件。

**参数：**
- `event_type` (str): 事件类型，支持通配符`*`
- `handler` (Callable): 事件处理函数，接收`Event`对象

**示例：**
```python
def handle_alert(event):
    print(f"收到告警: {event.type}")

bus.subscribe("alert.*", handle_alert)
bus.subscribe("*", handle_all)  # 订阅所有事件
```

### `emit(event: Event)`

发射事件。

**参数：**
- `event` (Event): 事件对象

**示例：**
```python
from aios.core.event import Event

event = Event.create(
    event_type="alert.cpu_high",
    source="sensor",
    payload={"value": 95}
)
bus.emit(event)
```

### `get_event_bus() -> EventBus`

获取全局EventBus单例。

```python
from aios.core.event_bus import get_event_bus

bus = get_event_bus()
```

---

## Event API

### `Event`

事件数据类。

**字段：**
```python
@dataclass
class Event:
    id: str              # 唯一ID
    type: str            # 事件类型
    source: str          # 来源
    timestamp: int       # 毫秒时间戳
    payload: Dict        # 事件数据
```

### `Event.create(event_type, source, **payload) -> Event`

创建事件的便捷方法。

**参数：**
- `event_type` (str): 事件类型
- `source` (str): 来源
- `**payload`: 事件数据（关键字参数）

**示例：**
```python
event = Event.create(
    event_type="resource.cpu_high",
    source="sensor",
    value=95,
    threshold=80
)
```

### `event.to_dict() -> Dict`

转换为字典。

```python
data = event.to_dict()
# {"id": "...", "type": "...", ...}
```

---

## Scheduler API

### `ToyScheduler(bus: EventBus)`

创建Scheduler实例。

```python
from aios.core.toy_scheduler import ToyScheduler

scheduler = ToyScheduler(bus)
scheduler.start()
```

### `start()`

启动Scheduler，开始监听事件。

### `get_actions() -> List`

获取决策历史。

```python
actions = scheduler.get_actions()
```

---

## Reactor API

### `ToyReactor(bus: EventBus)`

创建Reactor实例。

```python
from aios.core.toy_reactor import ToyReactor

reactor = ToyReactor(bus)
reactor.start()
```

### `start()`

启动Reactor，开始监听决策事件。

### `get_executions() -> List`

获取执行历史。

```python
executions = reactor.get_executions()
```

---

## ScoreEngine API

### `ToyScoreEngine(bus: EventBus)`

创建ScoreEngine实例。

```python
from aios.core.toy_score_engine import ToyScoreEngine

score_engine = ToyScoreEngine(bus)
score_engine.start()
```

### `start()`

启动ScoreEngine，开始监听所有事件。

### `get_score() -> float`

获取当前评分（0-1）。

```python
score = score_engine.get_score()
# 0.75
```

### `get_stats() -> Dict`

获取统计数据。

```python
stats = score_engine.get_stats()
# {
#     "total_events": 100,
#     "success_count": 80,
#     "failure_count": 20,
#     ...
# }
```

### `get_history() -> List`

获取评分历史。

```python
history = score_engine.get_history()
# [
#     {"timestamp": 1234567890, "score": 0.8},
#     {"timestamp": 1234567900, "score": 0.75},
#     ...
# ]
```

---

## AgentStateMachine API

### `AgentStateMachine(agent_id: str, bus: EventBus)`

创建Agent状态机。

```python
from aios.core.agent_state_machine import AgentStateMachine

agent = AgentStateMachine("agent-001", bus)
```

### `start_task(task: str) -> bool`

开始任务。

**参数：**
- `task` (str): 任务描述

**返回：**
- `bool`: 是否成功开始

```python
success = agent.start_task("处理数据")
```

### `complete_task(success: bool)`

完成任务。

**参数：**
- `success` (bool): 是否成功

```python
agent.complete_task(success=True)
```

### `fail_task(error: str)`

任务失败。

**参数：**
- `error` (str): 错误信息

```python
agent.fail_task("timeout")
```

### `get_state() -> AgentState`

获取当前状态。

```python
from aios.core.agent_state_machine import AgentState

state = agent.get_state()
# AgentState.IDLE / RUNNING / DEGRADED / LEARNING
```

### `get_stats() -> Dict`

获取统计数据。

```python
stats = agent.get_stats()
# {
#     "tasks_completed": 10,
#     "tasks_failed": 2,
#     "degraded_count": 1,
#     ...
# }
```

---

## Memory Palace API

### `memory`

全局Memory API单例。

```python
from aios.memory.api import memory
```

### `store_lesson(category, pattern, lesson, **metadata) -> str`

存储教训。

**参数：**
- `category` (str): 错误类别
- `pattern` (str): 错误模式
- `lesson` (str): 教训内容
- `**metadata`: 额外元数据

**返回：**
- `str`: 教训ID

**示例：**
```python
lesson_id = memory.store_lesson(
    category="timeout",
    pattern="network_error",
    lesson="增加重试机制，使用指数退避",
    severity="high",
    source="autolearn"
)
```

### `find_similar(query, limit=5) -> List[Dict]`

查找相似教训。

**参数：**
- `query` (str): 查询文本
- `limit` (int): 返回结果数量

**返回：**
- `List[Dict]`: 相似教训列表

**示例：**
```python
results = memory.find_similar("超时", limit=3)
# [
#     {
#         "id": "timeout_1234567890",
#         "category": "timeout",
#         "lesson": "增加重试机制...",
#         "score": 2
#     },
#     ...
# ]
```

### `link(entity1, entity2, relation)`

建立实体关系。

**参数：**
- `entity1` (str): 实体1
- `entity2` (str): 实体2
- `relation` (str): 关系类型

**示例：**
```python
memory.link("timeout", "network_error", "causes")
memory.link("agent_error", "timeout", "related_to")
```

### `switch_backend(backend: MemoryBackend)`

切换后端。

**参数：**
- `backend` (MemoryBackend): 后端类型

**示例：**
```python
from aios.memory.api import MemoryBackend

memory.switch_backend(MemoryBackend.JSON)    # 文件系统
memory.switch_backend(MemoryBackend.CHROMA)  # 向量数据库
memory.switch_backend(MemoryBackend.NEO4J)   # 图数据库
```

### `get_memory(backend) -> MemoryAPI`

获取Memory API实例。

```python
from aios.memory.api import get_memory, MemoryBackend

mem = get_memory(MemoryBackend.JSON)
```

---

## 自动化API

### 自动系统维护

```python
from aios.maintenance.auto_cleanup import main as cleanup

# 运行清理
cleanup()
```

**输出：**
- `CLEANUP_OK` - 正常
- `CLEANUP_WARNING` - 磁盘 >80%
- `CLEANUP_CRITICAL` - 磁盘 >90%

### 自动知识提取

```python
from aios.learning.knowledge_extractor import main as extract

# 运行知识提取
extract()
```

**输出：**
- `KNOWLEDGE_OK` - 无新知识
- `KNOWLEDGE_EXTRACTED:N` - 提取了N条教训

### 自动性能优化

```python
from aios.learning.performance_optimizer import main as optimize

# 运行性能优化
optimize()
```

**输出：**
- `PERF_OK` - 性能正常
- `PERF_OPTIMIZED:N` - 应用了N个优化
- `PERF_DEGRADED` - 发现严重问题

### Evolution Score快照

```python
from aios.learning.baseline import snapshot

# 获取快照
data = snapshot()
# {
#     "evolution_score": 0.45,
#     "grade": "healthy",
#     "total_events": 100,
#     ...
# }
```

---

## 事件类型参考

### 系统事件

- `system.heartbeat` - 心跳事件
- `system.startup` - 系统启动
- `system.shutdown` - 系统关闭

### 资源事件

- `resource.cpu_high` - CPU高占用
- `resource.memory_high` - 内存高占用
- `resource.disk_full` - 磁盘满

### Agent事件

- `agent_error` - Agent错误
- `agent.task_started` - 任务开始
- `agent.task_completed` - 任务完成
- `agent.task_failed` - 任务失败
- `agent.state_changed` - 状态变化

### Scheduler事件

- `scheduler.decision` - 决策事件

### Reactor事件

- `reactor.fix_started` - 修复开始
- `reactor.fix_completed` - 修复完成
- `reactor.fix_failed` - 修复失败

### ScoreEngine事件

- `score.updated` - 评分更新
- `score.degraded` - 系统降级
- `score.recovered` - 系统恢复

---

## 配置文件

### playbooks.json

Playbook规则配置。

```json
{
  "id": "cpu_spike",
  "name": "CPU峰值处理",
  "trigger": {
    "type": "resource.cpu_high"
  },
  "actions": [
    {"type": "降低优先级进程"},
    {"type": "清理缓存"}
  ],
  "cooldown_minutes": 5,
  "enabled": true
}
```

### HEARTBEAT.md

心跳任务配置。

```markdown
## 每天：自动系统维护
- 运行 auto_cleanup.py
- 清理 >7天的 events.jsonl
- 归档 >30天的 memory/*.md
```

---

## 错误处理

### 常见异常

**`EventBusError`**
- EventBus相关错误

**`SchedulerError`**
- Scheduler决策错误

**`ReactorError`**
- Reactor执行错误

**`MemoryError`**
- Memory操作错误

### 错误处理示例

```python
try:
    memory.store_lesson(...)
except MemoryError as e:
    print(f"存储失败: {e}")
    # 降级处理
```

---

## 最佳实践

### 1. 事件命名

使用层级结构：
```python
# 好
"resource.cpu.high"
"agent.task.completed"

# 不好
"cpu_high"
"task_done"
```

### 2. 错误处理

总是捕获异常：
```python
try:
    bus.emit(event)
except Exception as e:
    logger.error(f"发射事件失败: {e}")
```

### 3. 资源清理

使用上下文管理器：
```python
with EventBus() as bus:
    # 使用bus
    pass
# 自动清理
```

### 4. 测试

为关键路径编写测试：
```python
def test_full_flow():
    bus = EventBus()
    scheduler = ToyScheduler(bus)
    reactor = ToyReactor(bus)
    
    # 测试完整流程
    ...
```

---

## 性能优化

### 1. 批量操作

```python
# 批量发射事件
events = [Event.create(...) for _ in range(100)]
for event in events:
    bus.emit(event)
```

### 2. 异步处理

```python
import asyncio

async def handle_event_async(event):
    # 异步处理
    await asyncio.sleep(0.1)
    return result
```

### 3. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_operation(key):
    # 昂贵操作
    return result
```

---

## 版本兼容性

### v0.5

- ✅ Memory Palace API
- ✅ 自动化三连击
- ✅ 完整测试覆盖

### v0.4

- ✅ 插件系统
- ✅ Dashboard v1.0

### v0.3

- ✅ 感知层（Sensors + Dispatcher）

### v0.2

- ✅ 5层事件架构

---

## 参考资料

- [README.md](../README.md) - 快速开始
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [TUTORIAL.md](TUTORIAL.md) - 从零搭建
- [CONTRIBUTING.md](../CONTRIBUTING.md) - 贡献指南

---

**版本：** v0.5  
**更新日期：** 2026-02-24  
**作者：** 珊瑚海 + 小九
