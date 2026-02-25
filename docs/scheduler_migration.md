# Scheduler 迁移指南：ToyScheduler → SchedulerV2

## 概述

`scheduler_v2.py` 是 `toy_scheduler.py` 的 drop-in replacement，新增优先级队列、并发控制和超时重试，同时保持 100% 向后兼容。

## 快速迁移（零改动）

```python
# 之前
from core.toy_scheduler import ToyScheduler, start_scheduler

# 之后（二选一）
from core.scheduler_v2 import ToyScheduler, start_scheduler   # 别名兼容
from core.scheduler_v2 import SchedulerV2, start_scheduler     # 推荐
```

所有现有代码无需修改：`start()`, `get_actions()`, 事件订阅行为完全一致。

## 新增能力

### 1. 优先级队列（P0/P1/P2）

```python
from core.scheduler_v2 import SchedulerV2, Task, Priority

scheduler = SchedulerV2()
scheduler.start()

# P0 = 紧急（资源临界）, P1 = 高（agent 错误）, P2 = 普通
scheduler.submit(Task(name="critical_fix", priority=Priority.P0, handler=my_fn))
scheduler.submit(Task(name="log_cleanup", priority=Priority.P2, handler=cleanup_fn))
```

排序规则：优先级 > 等待时间（FIFO）> 插入顺序。

### 2. 并发控制

```python
# 默认最多 5 个任务并行
scheduler = SchedulerV2(max_concurrency=3)  # 自定义
```

### 3. 超时 + 自动重试

```python
scheduler.submit(Task(
    name="flaky_api_call",
    handler=call_api,
    timeout_sec=10,     # 10 秒超时
    max_retries=2,      # 最多重试 2 次
))
```

### 4. 统计信息

```python
stats = scheduler.get_stats()
# {'queued': 0, 'running': 1, 'completed': 5, 'failed': 0, 'timed_out': 0, ...}
```

## API 对照表

| ToyScheduler | SchedulerV2 | 说明 |
|---|---|---|
| `ToyScheduler(bus)` | `SchedulerV2(bus, max_concurrency)` | 新增并发参数 |
| `start()` | `start()` | 相同 |
| `get_actions()` | `get_actions()` | 相同 |
| — | `submit(task)` | 新增 |
| — | `stop()` | 新增 |
| — | `get_stats()` | 新增 |
| — | `get_queue_size()` | 新增 |
| — | `get_running_count()` | 新增 |
| — | `get_completed_tasks()` | 新增 |

## 事件变更

新增事件类型（不影响现有事件）：

| 事件 | 触发时机 |
|---|---|
| `scheduler.task_submitted` | 任务入队 |
| `scheduler.task_started` | 任务开始执行 |
| `scheduler.task_completed` | 任务成功完成 |
| `scheduler.task_failed` | 任务最终失败 |
| `scheduler.task_retrying` | 任务重试 |

原有 `scheduler.decision` 事件保持不变。

## 测试

```bash
py -m pytest tests/test_scheduler_v2.py -v
```

34 个测试覆盖：优先级排序、并发控制、超时、重试、向后兼容、事件发射、边界情况。

## 文件清单

| 文件 | 说明 |
|---|---|
| `core/scheduler_v2.py` | 新调度器实现 |
| `tests/test_scheduler_v2.py` | 完整测试套件 |
| `core/toy_scheduler.py` | 旧实现（保留，不修改） |
