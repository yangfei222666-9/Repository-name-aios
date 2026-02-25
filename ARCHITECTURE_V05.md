# AIOS v0.5 架构升级：从 Monitor 到 Autonomous System

## 核心突破

从 **被动监控** 升级到 **主动自治**

### 之前（v0.4）
```
Monitor → Display → Human Decision
```
- 只能看，不能做
- 需要人工判断
- 系统是"死"的

### 现在（v0.5）
```
Monitor → Judge → Trigger → Fix → Verify → Update Score
```
- 自己看、自己想、自己做
- 自动判断和执行
- 系统是"活"的

## 架构图

```
                Event Bus
                    |
        +-----------+-----------+
        |                       |
    Monitor                Scheduler
        |                       |
        +--------> Reactor <----+
                      |
                      v
                 Agent Pool
                 Pipeline
                 Score Engine
                 Dashboard
```

## 核心组件

### 1. Event Bus（事件总线）

**作用：** 统一数据流，解耦模块

**API：**
```python
from event_bus import emit, subscribe, EventType

# 发射事件
emit(EventType.TASK_STARTED, {
    "task_id": "task-001",
    "agent": "coder"
})

# 订阅事件
def on_task_started(event):
    print(f"任务开始: {event['data']['task_id']}")

subscribe(EventType.TASK_STARTED, on_task_started)
```

**事件类型：**
- Agent 生命周期：created, started, idle, running, blocked, degraded, stopped, failed
- 任务事件：created, started, completed, failed, timeout
- 资源事件：spike, low, critical
- 系统事件：healthy, degraded, critical
- Pipeline 事件：started, completed, failed
- Reactor 事件：triggered, executed, failed

### 2. Scheduler（调度核心）

**作用：** 自动决策和调度

**流程：**
```
1. Monitor（监控）
   - 检查 CPU/内存/GPU
   - 检查 Agent 状态
   - 检查任务队列

2. Judge（判断）
   - 分析最近事件
   - 计算风险等级
   - 生成决策列表

3. Trigger（触发）
   - 发射 Reactor 事件
   - 调用修复动作

4. Verify（验证）
   - 检查修复效果
   - 记录成功/失败

5. Update Score（更新评分）
   - 重新计算 Evolution Score
   - 更新系统状态
```

**决策规则：**
- CPU > 80% → 降低并发
- 内存 > 75% → 清理缓存
- 错误率 > 30% → 减少负载
- Agent 降级 → 减少任务分配
- 任务超时 → 取消并重新调度

### 3. Agent 状态机

**状态：**
- **idle**：空闲，等待任务
- **running**：运行中
- **blocked**：阻塞（等待资源/依赖）
- **degraded**：降级（性能下降）
- **failed**：失败

**状态转换：**
```
idle → running → completed → idle
     ↓
   blocked → running
     ↓
   degraded → running / failed
     ↓
   failed → idle (重启)
```

## 集成方式

### 方式 1：集成到 Pipeline

在 `pipeline.py` 中添加：

```python
from event_bus import emit, EventType

def run_pipeline():
    # 发射开始事件
    emit(EventType.PIPELINE_STARTED, {
        "timestamp": datetime.now().isoformat()
    })
    
    # ... 执行各阶段 ...
    
    # 发射完成事件
    emit(EventType.PIPELINE_COMPLETED, {
        "duration_ms": total_ms,
        "stages": stages
    })
```

### 方式 2：集成到 Reactor

在 `reactor_auto_trigger.py` 中添加：

```python
from event_bus import emit, EventType

def execute_playbook(playbook, event):
    # 发射触发事件
    emit(EventType.REACTOR_TRIGGERED, {
        "playbook_id": playbook['id'],
        "event_id": event.get('epoch')
    })
    
    # ... 执行 playbook ...
    
    # 发射执行结果
    if success:
        emit(EventType.REACTOR_EXECUTED, result)
    else:
        emit(EventType.REACTOR_FAILED, result)
```

### 方式 3：集成到 Agent System

在 `agent_system/pool.py` 中添加：

```python
from event_bus import emit, EventType

class Agent:
    def __init__(self, ...):
        self.state = "idle"
        emit(EventType.AGENT_CREATED, {"agent_id": self.id})
    
    def start_task(self, task):
        self.state = "running"
        emit(EventType.AGENT_STARTED, {
            "agent_id": self.id,
            "task_id": task.id
        })
    
    def complete_task(self):
        self.state = "idle"
        emit(EventType.TASK_COMPLETED, {
            "agent_id": self.id,
            "duration_ms": duration
        })
```

## 启动方式

### 1. 启动 Scheduler（后台）

```powershell
cd C:\Users\A\.openclaw\workspace\aios
Start-Process -WindowStyle Hidden "C:\Program Files\Python312\python.exe" -ArgumentList "-X utf8 scheduler.py"
```

### 2. 集成到 HEARTBEAT

在 `HEARTBEAT.md` 添加：

```markdown
### 每次心跳：Scheduler 检查
- Scheduler 自动运行（后台进程）
- 监控系统状态
- 自动触发 Reactor
- 静默执行，除非有 critical 决策
```

## 测试场景

### 场景 1：资源峰值自动响应

```python
# 模拟 CPU 峰值
emit(EventType.RESOURCE_SPIKE, {
    "resource": "cpu",
    "value": 85,
    "threshold": 80
})

# Scheduler 自动响应：
# 1. 收到事件
# 2. 判断需要干预
# 3. 触发 Reactor
# 4. 执行降低并发
# 5. 验证效果
# 6. 更新评分
```

### 场景 2：任务失败自动重试

```python
# 模拟任务失败
emit(EventType.TASK_FAILED, {
    "task_id": "task-001",
    "error": "Connection timeout"
})

# Scheduler 自动响应：
# 1. 收到事件
# 2. 判断可重试
# 3. 触发重试
# 4. 记录结果
```

## 关键指标

- **响应时间**：< 1 秒（从事件到决策）
- **决策准确率**：> 90%
- **自动修复率**：> 70%
- **误报率**：< 5%

## 下一步优化

1. **学习最优决策**
   - 记录每次决策的效果
   - 自动调整决策规则
   - A/B 测试不同策略

2. **预测性调度**
   - 根据历史数据预测负载
   - 提前分配资源
   - 避免峰值

3. **多 Agent 协作**
   - Agent 之间通过事件通信
   - 自动负载均衡
   - 故障转移

4. **自适应阈值**
   - 根据系统特性调整阈值
   - 不同时段不同策略
   - 自动优化

## 总结

**v0.4 → v0.5 的关键突破：**

- ✅ 从"监控系统"到"自治系统"
- ✅ 从"被动响应"到"主动决策"
- ✅ 从"人工干预"到"自动修复"
- ✅ 从"单体架构"到"事件驱动"

**AIOS 现在真正"活"了！**
