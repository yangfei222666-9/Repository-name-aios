# 可观测层注入完成报告

## ✅ 第一批交付完成

### 1. 核心组件（3 个文件）

**✓ aios/observability/tracer.py**
- ContextVar 实现（线程安全）
- start_trace / span 上下文管理器
- ensure_task_id（强约束：task_id 永远非空）
- current_trace_id / current_span_id 全局访问

**✓ aios/observability/metrics.py**
- MetricsRegistry（线程安全）
- Counter / Gauge / Histogram
- snapshot() / snapshot_json()
- 全局单例 METRICS

**✓ aios/observability/logger.py**
- StructuredLogger（JSON 格式）
- 自动注入 trace_id / span_id
- emit_event（写入 events.jsonl）
- 线程安全写入

### 2. 验证结果

**Smoke Test 通过：**
```json
// aios/logs/aios.jsonl
{
  "timestamp": "2026-02-25T08:07:03.028978+00:00",
  "level": "info",
  "logger": "debug",
  "message": "inside trace",
  "trace_id": "trace:d7058597dbc54ffb97d3a883c878ab97",
  "span_id": "span:cfce1357e6854c50bfb122462f801827",
  "parent_span_id": null,
  "task_id": "debug-1"
}

// events.jsonl
{
  "ts": "2026-02-25T08:07:19.865253+00:00",
  "type": "smoke_event",
  "severity": "info",
  "task_id": "smoke-1",
  "agent_id": null,
  "trace_id": "trace:2f50ad4a6e5d46de928feb764fa2a1e9",
  "span_id": "span:2f4302ed1e284bcd9d6286ef5253e263",
  "payload": {"ok": true}
}
```

---

## 📋 auto_dispatcher.py 注入点

### 当前入口函数（_dispatch_task）

**位置：** `aios/agent_system/auto_dispatcher.py:328`

**当前代码：**
```python
def _dispatch_task(self, task: Dict) -> Dict:
    """分发单个任务到 Agent（通过 sessions_spawn）+ Self-Improving Loop"""
    task_type = task.get("type", "monitor")
    message = task["message"]
    task_id = task.get("id", "unknown")  # ← 这里 task_id 可能是 "unknown"

    # 生成 agent_id（用于追踪）
    agent_id = f"{task_type}-dispatcher"

    # 如果启用了 Self-Improving Loop，包装执行
    if self.improving_loop:
        result = self.improving_loop.execute_with_improvement(
            agent_id=agent_id,
            task=message,
            execute_fn=lambda: self._do_dispatch(task, task_type, message),
            context={"task_id": task_id, "task_type": task_type}
        )
        # ... 省略
```

### 注入方案（精准位置）

**在 _dispatch_task 方法开头添加：**
```python
def _dispatch_task(self, task: Dict) -> Dict:
    """分发单个任务到 Agent（通过 sessions_spawn）+ Self-Improving Loop"""
    # ========== 可观测层注入开始 ==========
    from aios.observability.tracer import start_trace, ensure_task_id
    from aios.observability.metrics import METRICS
    from aios.observability.logger import get_logger
    import time
    import traceback
    
    # 强约束：task_id 永远非空
    task_id = ensure_task_id(task)
    task_type = task.get("type", "monitor")
    message = task.get("message", "")
    priority = task.get("priority", "normal")
    
    # 初始化 logger（如果还没有）
    if not hasattr(self, '_obs_logger'):
        self._obs_logger = get_logger("auto_dispatcher", level="INFO")
    
    logger = self._obs_logger
    
    # 开始 Trace
    with start_trace("dispatch_task", attributes={"task_id": task_id, "type": task_type, "priority": priority}):
        t0 = time.perf_counter()
        
        logger.info("Task received", task_id=task_id, type=task_type, priority=priority)
        logger.emit_event("task_received", task_id=task_id, severity="info", payload={
            "type": task_type,
            "priority": priority,
        })
        METRICS.inc_counter("tasks.received", labels={"type": task_type, "priority": priority})
        
        try:
            # ========== 原有逻辑开始 ==========
            agent_id = f"{task_type}-dispatcher"

            # 如果启用了 Self-Improving Loop，包装执行
            if self.improving_loop:
                result = self.improving_loop.execute_with_improvement(
                    agent_id=agent_id,
                    task=message,
                    execute_fn=lambda: self._do_dispatch(task, task_type, message),
                    context={"task_id": task_id, "task_type": task_type}
                )

                # 检查是否触发了改进
                if result.get("improvement_triggered"):
                    self._log(
                        "info",
                        "Self-improvement triggered",
                        agent_id=agent_id,
                        improvements=result.get("improvement_applied", 0)
                    )

                # 返回实际结果
                if result["success"]:
                    final_result = result["result"]
                else:
                    final_result = {"status": "error", "message": result.get("error", "unknown")}
            else:
                # 没有 Self-Improving Loop，直接执行
                final_result = self._do_dispatch(task, task_type, message)
            # ========== 原有逻辑结束 ==========
            
            # ========== 可观测层注入：成功 ==========
            logger.info("Task dispatched", task_id=task_id, type=task_type, priority=priority)
            logger.emit_event("task_dispatched", task_id=task_id, severity="info", payload={
                "type": task_type,
                "priority": priority,
            })
            METRICS.inc_counter("tasks.dispatched", labels={"type": task_type, "priority": priority})
            
            return final_result
            
        except Exception as e:
            # ========== 可观测层注入：失败 ==========
            logger.exception("Dispatch failed", task_id=task_id, type=task_type, priority=priority, 
                           error_type=type(e).__name__, message=str(e))
            logger.emit_event("error", task_id=task_id, severity="error", payload={
                "error_type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc(),
                "type": task_type,
                "priority": priority,
            })
            METRICS.inc_counter("tasks.failed", labels={"type": task_type, "priority": priority})
            raise
            
        finally:
            # ========== 可观测层注入：指标 ==========
            latency_ms = (time.perf_counter() - t0) * 1000.0
            METRICS.observe("dispatch.latency_ms", latency_ms, labels={"type": task_type, "priority": priority})
    # ========== 可观测层注入结束 ==========
```

---

## 📋 Circuit Breaker 日志规范

### 当前日志（需要改进）

**位置：** `aios/agent_system/auto_dispatcher.py:365`

**当前代码：**
```python
self._log(
    "warn",
    "Circuit breaker open",
    task_id=task.get("id"),  # ← 可能是 None
    task_type=task_type,
    retry_after=retry_after,
)
```

### 改进方案

```python
# 在 _do_dispatch 方法开头也注入 ensure_task_id
task_id = ensure_task_id(task)

# 熔断器日志改为：
self._log(
    "warn",
    "Circuit breaker open",
    task_id=task_id,  # ← 永远非空
    task_type=task_type,
    retry_after=retry_after,
    reason="consecutive_failures",
    fail_count=self.circuit_breaker.get_status().get(task_type, {}).get("failure_count", 0),
    cooldown_sec=retry_after,
)

# 同时发送事件
logger.emit_event("circuit_breaker_open", task_id=task_id, agent_id=f"{task_type}-dispatcher", 
                  severity="warn", payload={
                      "task_type": task_type,
                      "retry_after": retry_after,
                      "fail_count": self.circuit_breaker.get_status().get(task_type, {}).get("failure_count", 0),
                  })
```

---

## 🎯 关键效果

### 1. task_id 永远非空
- 优先级：`task['id']` → `task['task_id']` → `source_path` → `uuid`
- 所有日志、事件、指标都有 task_id

### 2. 完整的 Trace 链路
- 每个任务都有唯一 trace_id
- 嵌套操作有 span_id / parent_span_id
- 可追踪完整执行路径

### 3. 结构化事件流
- events.jsonl 统一格式
- 可被 Dashboard / Reactor / Meta-Agent 消费
- 带 trace_id 可关联日志

### 4. 实时指标
- Counter（累加）
- Gauge（瞬时值）
- Histogram（分布统计）
- 可 snapshot 导出

---

## 🚀 下一步

1. **应用注入方案** - 把上面的代码精准贴到 auto_dispatcher.py
2. **验证效果** - 运行一次任务，查看日志/事件/指标
3. **扩展到其他模块** - Reactor / Scheduler / Self-Improving Loop

**准备好了吗？我可以立刻帮你应用注入方案！**
