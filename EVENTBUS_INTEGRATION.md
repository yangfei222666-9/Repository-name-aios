# EventBus 集成指南 - 分水岭升级

## 为什么这是分水岭？

**之前：** 模块直接调用，紧耦合  
**之后：** 事件驱动，松耦合

这是从"玩具项目"到"系统设计"的关键一步。

## 最小 EventBus（50 行）

```python
from event_bus_mini import emit, on

# 订阅事件
on("task.started", lambda e: print(f"任务开始: {e['task_id']}"))

# 发射事件
emit("task.started", task_id="t001", agent="coder")
```

## 集成步骤

### 1. Pipeline 集成

**之前：**
```python
def run_pipeline():
    # 直接执行
    result = stage_sensors()
    # ...
```

**之后：**
```python
from event_bus_mini import emit

def run_pipeline():
    emit("pipeline.started")
    
    result = stage_sensors()
    emit("stage.completed", stage="sensors", duration_ms=100)
    
    # ...
    
    emit("pipeline.completed", total_ms=1000)
```

### 2. Reactor 集成

**之前：**
```python
def execute_playbook(playbook):
    # 直接执行
    result = subprocess.run(...)
```

**之后：**
```python
from event_bus_mini import emit

def execute_playbook(playbook):
    emit("reactor.triggered", playbook_id=playbook['id'])
    
    result = subprocess.run(...)
    
    if result.returncode == 0:
        emit("reactor.success", playbook_id=playbook['id'])
    else:
        emit("reactor.failed", playbook_id=playbook['id'], error=result.stderr)
```

### 3. Agent 集成

**之前：**
```python
class Agent:
    def start_task(self, task):
        # 直接执行
        self.status = "running"
```

**之后：**
```python
from event_bus_mini import emit

class Agent:
    def start_task(self, task):
        self.status = "running"
        emit("agent.started", agent_id=self.id, task_id=task.id)
    
    def complete_task(self):
        self.status = "idle"
        emit("agent.completed", agent_id=self.id, duration_ms=1500)
```

### 4. Scheduler 监听

**核心：** Scheduler 不再主动轮询，而是被动监听事件

```python
from event_bus_mini import on, emit

class Scheduler:
    def __init__(self):
        # 订阅关键事件
        on("reactor.failed", self.handle_reactor_failed)
        on("agent.degraded", self.handle_agent_degraded)
        on("resource.spike", self.handle_resource_spike)
    
    def handle_reactor_failed(self, event):
        # 决策：重试或降级
        emit("decision.made", action="retry", reason="reactor_failed")
    
    def handle_agent_degraded(self, event):
        # 决策：减少负载
        emit("decision.made", action="reduce_load", agent_id=event['agent_id'])
    
    def handle_resource_spike(self, event):
        # 决策：降低并发
        emit("decision.made", action="reduce_concurrency", resource=event['resource'])
```

## 事件命名规范

```
<模块>.<动作>

例如：
- pipeline.started
- pipeline.completed
- pipeline.failed

- reactor.triggered
- reactor.success
- reactor.failed

- agent.created
- agent.started
- agent.idle
- agent.running
- agent.blocked
- agent.degraded
- agent.completed
- agent.failed

- task.created
- task.started
- task.completed
- task.failed
- task.timeout

- resource.spike
- resource.low
- resource.critical

- decision.made
- decision.executed
- decision.verified
```

## 实战：3 步完成集成

### 步骤 1：在 pipeline.py 顶部添加

```python
from event_bus_mini import emit
```

### 步骤 2：在关键位置发射事件

```python
def run_pipeline():
    emit("pipeline.started")  # 👈 添加这行
    
    # ... 原有代码 ...
    
    emit("pipeline.completed", total_ms=total_ms)  # 👈 添加这行
```

### 步骤 3：在 scheduler.py 中监听

```python
from event_bus_mini import on

on("pipeline.completed", lambda e: print(f"✅ Pipeline 完成: {e['total_ms']}ms"))
```

## 验证效果

运行 Pipeline 后，检查事件日志：

```powershell
Get-Content C:\Users\A\.openclaw\workspace\aios\events\bus.jsonl -Tail 10
```

应该看到：
```json
{"type":"pipeline.started","ts":"2026-02-23T20:00:00"}
{"type":"stage.completed","ts":"2026-02-23T20:00:01","stage":"sensors"}
{"type":"pipeline.completed","ts":"2026-02-23T20:00:05","total_ms":5000}
```

## 为什么这是分水岭？

### 之前的问题
- ❌ 模块紧耦合（Pipeline 直接调用 Reactor）
- ❌ 难以扩展（加新功能要改多处）
- ❌ 难以测试（无法单独测试）
- ❌ 难以监控（不知道发生了什么）

### 现在的优势
- ✅ 模块解耦（通过事件通信）
- ✅ 易于扩展（订阅新事件即可）
- ✅ 易于测试（模拟事件即可）
- ✅ 易于监控（所有事件都有日志）

## 下一步

1. **集成到 Pipeline**（5 分钟）
2. **集成到 Reactor**（5 分钟）
3. **集成到 Agent System**（10 分钟）
4. **启动 Scheduler 监听**（1 分钟）

**总共 20 分钟，系统架构升级完成。**

## 最终效果

```
Pipeline 运行
  ↓ emit("pipeline.started")
  ↓
Scheduler 收到事件
  ↓ 判断：需要监控
  ↓ emit("monitor.started")
  ↓
Monitor 收到事件
  ↓ 检查资源
  ↓ emit("resource.spike", cpu=85)
  ↓
Scheduler 收到事件
  ↓ 判断：需要干预
  ↓ emit("reactor.trigger", action="reduce_concurrency")
  ↓
Reactor 收到事件
  ↓ 执行 playbook
  ↓ emit("reactor.success")
  ↓
Scheduler 收到事件
  ↓ 验证效果
  ↓ emit("decision.verified", score=0.9)
  ↓
Dashboard 收到事件
  ↓ 更新显示
```

**这就是事件驱动架构的威力。**

---

**这是从"玩具"到"系统"的分水岭。**
