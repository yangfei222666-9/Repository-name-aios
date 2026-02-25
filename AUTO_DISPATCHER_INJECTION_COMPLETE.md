# Auto Dispatcher 可观测层注入完成

## ✅ 注入位置标注

### 1. 导入部分（第 11-20 行）

```python
# ========== 可观测层导入（新增）==========
try:
    from aios.observability.tracer import start_trace, span, ensure_task_id, current_trace_id
    from aios.observability.metrics import METRICS
    from aios.observability.logger import get_logger
    OBSERVABILITY_ENABLED = True
except ImportError:
    OBSERVABILITY_ENABLED = False
    print("[WARN] Observability layer not available")
# ==========================================
```

### 2. __init__ 方法（第 56-60 行）

```python
# ========== 可观测层初始化（新增）==========
if OBSERVABILITY_ENABLED:
    self._obs_logger = get_logger("auto_dispatcher", level="INFO")
else:
    self._obs_logger = None
# ==========================================
```

### 3. _dispatch_task 方法（完整重写，第 200-290 行）

**核心注入点：**
- `ensure_task_id(task)` - 强约束 task_id 永远非空
- `start_trace()` - 开始分布式追踪
- `logger.info()` + `logger.emit_event()` - 结构化日志 + 事件
- `METRICS.inc_counter()` + `METRICS.observe()` - 实时指标
- `try/except/finally` - 完整的成功/失败/指标记录

### 4. _do_dispatch 方法（第 292-380 行）

**Circuit Breaker 增强：**
```python
# ========== 可观测层：Circuit Breaker 日志（新增）==========
if logger:
    logger.warn(
        "Circuit breaker open",
        task_id=task_id,
        task_type=task_type,
        retry_after=retry_after,
        reason="consecutive_failures",
        fail_count=fail_count,
        cooldown_sec=retry_after,
    )
    logger.emit_event("circuit_breaker_open", task_id=task_id, agent_id=f"{task_type}-dispatcher", 
                    severity="warn", payload={
                        "task_type": task_type,
                        "retry_after": retry_after,
                        "fail_count": fail_count,
                    })
    METRICS.inc_counter("circuit_breaker.open", labels={"type": task_type})
# ==========================================
```

### 5. status 方法（第 450 行）

```python
return {
    ...
    "observability": "enabled" if OBSERVABILITY_ENABLED else "disabled",  # 新增
}
```

---

## 🔥 关键改进

### 1. task_id 永远非空
- 使用 `ensure_task_id(task)` 强约束
- 优先级：`task['id']` → `task['task_id']` → `source_path` → `uuid`

### 2. 完整的 Trace 链路
- 每个任务都有唯一 `trace_id`
- 嵌套操作有 `span_id` / `parent_span_id`

### 3. 结构化事件流
- `events.jsonl` 统一格式
- 带 `trace_id` 可关联日志

### 4. Circuit Breaker 增强
- 带 `reason` / `fail_count` / `cooldown_sec`
- 发送 `circuit_breaker_open` 事件
- 记录 `circuit_breaker.open` 指标

### 5. 实时指标
- `tasks.received` - 收到任务数
- `tasks.dispatched` - 分发成功数
- `tasks.failed` - 失败任务数
- `dispatch.latency_ms` - 分发延迟（Histogram）
- `circuit_breaker.open` - 熔断器触发次数

---

## 📊 输出示例

### 日志（aios/logs/aios.jsonl）
```json
{
  "timestamp": "2026-02-25T08:10:15.123456+00:00",
  "level": "info",
  "logger": "auto_dispatcher",
  "message": "Task received",
  "trace_id": "trace:abc123def456",
  "span_id": "span:xyz789",
  "parent_span_id": null,
  "task_id": "task:1772007015123",
  "type": "code",
  "priority": "high"
}
```

### 事件（events.jsonl）
```json
{
  "ts": "2026-02-25T08:10:15.123456+00:00",
  "type": "task_received",
  "severity": "info",
  "task_id": "task:1772007015123",
  "agent_id": null,
  "trace_id": "trace:abc123def456",
  "span_id": "span:xyz789",
  "payload": {
    "type": "code",
    "priority": "high"
  }
}
```

### 指标（METRICS.snapshot()）
```json
{
  "counters": [
    {"name": "tasks.received", "labels": {"type": "code", "priority": "high"}, "value": 5},
    {"name": "tasks.dispatched", "labels": {"type": "code", "priority": "high"}, "value": 4},
    {"name": "tasks.failed", "labels": {"type": "code", "priority": "high"}, "value": 1}
  ],
  "histograms": [
    {
      "name": "dispatch.latency_ms",
      "labels": {"type": "code", "priority": "high"},
      "value": {"count": 5, "avg": 125.5, "p95": 250, "p99": 300}
    }
  ]
}
```

---

## 🚀 使用方式

### 替换原文件（生产环境）
```bash
# 备份原文件
cp aios/agent_system/auto_dispatcher.py aios/agent_system/auto_dispatcher_backup.py

# 替换为新版本
cp aios/agent_system/auto_dispatcher_v2.py aios/agent_system/auto_dispatcher.py
```

### 测试新版本
```bash
cd C:\Users\A\.openclaw\workspace\aios
python agent_system\auto_dispatcher_v2.py status
```

### 验证可观测性
```bash
# 查看日志
Get-Content aios\logs\aios.jsonl | Select-Object -Last 10

# 查看事件
Get-Content events.jsonl | Select-Object -Last 10

# 查看指标（需要手动触发 snapshot）
python -c "from aios.observability.metrics import METRICS; print(METRICS.snapshot_json())"
```

---

## ✅ 验收标准

运行一次任务后，你应该看到：

1. **✓ 日志有 trace_id / span_id / task_id**
2. **✓ events.jsonl 有 task_received / task_dispatched 事件**
3. **✓ Circuit Breaker 日志带 reason / fail_count**
4. **✓ 指标可以 snapshot 导出**
5. **✓ task_id 永远非空（不再是 null 或 unknown）**

---

**准备好了吗？立刻替换并测试！** 🚀
