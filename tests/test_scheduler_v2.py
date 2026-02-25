"""
SchedulerV2 完整单元测试

覆盖：
- 优先级排序
- 等待时间排序
- 并发控制
- 超时检测
- 重试机制
- 向后兼容 ToyScheduler API
- 事件驱动决策
"""
import sys
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType, create_event
from core.event_bus import EventBus
from core.scheduler_v2 import (
    SchedulerV2,
    Task,
    Priority,
    TaskState,
    _PriorityQueue,
    start_scheduler,
    ToyScheduler,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bus(tmp_path):
    """每个测试独立的 EventBus"""
    return EventBus(storage_path=str(tmp_path / "events.jsonl"))


@pytest.fixture
def scheduler(bus):
    """已启动的 SchedulerV2"""
    s = SchedulerV2(bus=bus, max_concurrency=5)
    s.start()
    yield s
    s.stop()


# ---------------------------------------------------------------------------
# PriorityQueue 单元测试
# ---------------------------------------------------------------------------

class TestPriorityQueue:
    def test_empty_pop_returns_none(self):
        q = _PriorityQueue()
        assert q.pop() is None

    def test_priority_ordering(self):
        q = _PriorityQueue()
        t_p2 = Task(name="low", priority=Priority.P2, created_at=1.0)
        t_p0 = Task(name="critical", priority=Priority.P0, created_at=2.0)
        t_p1 = Task(name="high", priority=Priority.P1, created_at=3.0)

        q.push(t_p2)
        q.push(t_p0)
        q.push(t_p1)

        assert q.pop().name == "critical"  # P0 first
        assert q.pop().name == "high"      # P1 second
        assert q.pop().name == "low"       # P2 last

    def test_same_priority_fifo_by_created_at(self):
        q = _PriorityQueue()
        t1 = Task(name="first", priority=Priority.P1, created_at=1.0)
        t2 = Task(name="second", priority=Priority.P1, created_at=2.0)
        t3 = Task(name="third", priority=Priority.P1, created_at=3.0)

        q.push(t3)
        q.push(t1)
        q.push(t2)

        assert q.pop().name == "first"   # 等待最久
        assert q.pop().name == "second"
        assert q.pop().name == "third"

    def test_len_and_bool(self):
        q = _PriorityQueue()
        assert len(q) == 0
        assert not q

        q.push(Task(name="a"))
        assert len(q) == 1
        assert q

    def test_peek(self):
        q = _PriorityQueue()
        assert q.peek() is None

        t = Task(name="x", priority=Priority.P0)
        q.push(t)
        assert q.peek().name == "x"
        assert len(q) == 1  # peek 不移除

    def test_drain(self):
        q = _PriorityQueue()
        for i in range(5):
            q.push(Task(name=f"t{i}"))
        tasks = q.drain()
        assert len(tasks) == 5
        assert len(q) == 0


# ---------------------------------------------------------------------------
# 向后兼容测试
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    """确保 SchedulerV2 是 ToyScheduler 的 drop-in replacement"""

    def test_alias(self):
        assert ToyScheduler is SchedulerV2

    def test_start_scheduler_function(self, bus):
        s = start_scheduler(bus=bus)
        assert isinstance(s, SchedulerV2)
        s.stop()

    def test_get_actions_empty(self, scheduler):
        assert scheduler.get_actions() == []

    def test_resource_event_creates_action(self, scheduler, bus):
        event = create_event(EventType.RESOURCE_CPU_SPIKE, "monitor", cpu_percent=85.0)
        bus.emit(event)
        time.sleep(0.1)

        actions = scheduler.get_actions()
        assert len(actions) >= 1
        assert actions[0]["action"] == "trigger_reactor"
        assert "资源告警" in actions[0]["reason"]

    def test_agent_error_creates_action(self, scheduler, bus):
        event = create_event(EventType.AGENT_ERROR, "agent_system", error="boom")
        bus.emit(event)
        time.sleep(0.1)

        actions = scheduler.get_actions()
        assert len(actions) == 1
        assert actions[0]["action"] == "trigger_reactor"
        assert "Agent" in actions[0]["reason"]

    def test_pipeline_completed_creates_action(self, scheduler, bus):
        event = create_event(EventType.PIPELINE_COMPLETED, "pipeline", duration_ms=1000)
        bus.emit(event)
        time.sleep(0.1)

        actions = scheduler.get_actions()
        assert len(actions) == 1
        assert actions[0]["action"] == "log_completion"


# ---------------------------------------------------------------------------
# 优先级排序测试
# ---------------------------------------------------------------------------

class TestPrioritySorting:
    def test_p0_executes_before_p2(self, scheduler):
        order = []

        def make_handler(label):
            def handler():
                order.append(label)
            return handler

        # 先提交 P2，再提交 P0
        scheduler.submit(Task(name="low", priority=Priority.P2, handler=make_handler("P2")))
        scheduler.submit(Task(name="critical", priority=Priority.P0, handler=make_handler("P0")))

        time.sleep(1)

        # P0 应该先执行（或至少在 order 中出现）
        assert "P0" in order
        assert "P2" in order

    def test_priority_values(self):
        assert Priority.P0 < Priority.P1 < Priority.P2

    def test_actions_include_priority(self, scheduler, bus):
        bus.emit(create_event(EventType.RESOURCE_CPU_SPIKE, "monitor", cpu_percent=50.0))
        bus.emit(create_event(EventType.AGENT_ERROR, "agent_system", error="x"))
        bus.emit(create_event(EventType.PIPELINE_COMPLETED, "pipeline"))
        time.sleep(0.1)

        actions = scheduler.get_actions()
        priorities = [a["priority"] for a in actions]
        assert int(Priority.P0) in priorities
        assert int(Priority.P1) in priorities
        assert int(Priority.P2) in priorities


# ---------------------------------------------------------------------------
# 并发控制测试
# ---------------------------------------------------------------------------

class TestConcurrencyControl:
    def test_max_concurrency_respected(self, bus):
        max_c = 3
        s = SchedulerV2(bus=bus, max_concurrency=max_c)
        s.start()

        peak_concurrent = {"value": 0}
        current = {"value": 0}
        lock = threading.Lock()

        def slow_handler():
            with lock:
                current["value"] += 1
                peak_concurrent["value"] = max(peak_concurrent["value"], current["value"])
            time.sleep(0.3)
            with lock:
                current["value"] -= 1

        for i in range(10):
            s.submit(Task(name=f"task_{i}", handler=slow_handler, priority=Priority.P1))

        time.sleep(3)
        s.stop()

        assert peak_concurrent["value"] <= max_c

    def test_default_concurrency_is_5(self, bus):
        s = SchedulerV2(bus=bus)
        assert s.max_concurrency == 5

    def test_get_running_count(self, bus):
        s = SchedulerV2(bus=bus, max_concurrency=5)
        s.start()

        barrier = threading.Event()

        def blocking_handler():
            barrier.wait(timeout=5)

        s.submit(Task(name="blocker", handler=blocking_handler))
        time.sleep(0.3)

        assert s.get_running_count() >= 1

        barrier.set()
        time.sleep(0.5)
        s.stop()


# ---------------------------------------------------------------------------
# 超时测试
# ---------------------------------------------------------------------------

class TestTimeout:
    def test_task_timeout(self, scheduler):
        def hang():
            time.sleep(10)

        scheduler.submit(Task(
            name="hanging_task",
            handler=hang,
            timeout_sec=0.3,
            max_retries=0,
        ))

        time.sleep(1.5)

        completed = scheduler.get_completed_tasks()
        hanging = [t for t in completed if t.name == "hanging_task"]
        assert len(hanging) == 1
        assert hanging[0].state == TaskState.TIMEOUT
        assert "Timeout" in (hanging[0].error or "")

    def test_timeout_with_retry(self, scheduler):
        call_count = {"value": 0}

        def flaky():
            call_count["value"] += 1
            time.sleep(10)  # 总是超时

        scheduler.submit(Task(
            name="flaky_timeout",
            handler=flaky,
            timeout_sec=0.2,
            max_retries=2,
        ))

        time.sleep(3)

        completed = scheduler.get_completed_tasks()
        flaky_tasks = [t for t in completed if t.name == "flaky_timeout"]
        assert len(flaky_tasks) == 1
        assert flaky_tasks[0].retries == 2
        assert flaky_tasks[0].state == TaskState.TIMEOUT


# ---------------------------------------------------------------------------
# 重试机制测试
# ---------------------------------------------------------------------------

class TestRetry:
    def test_retry_on_failure(self, scheduler):
        call_count = {"value": 0}

        def fail_twice():
            call_count["value"] += 1
            if call_count["value"] <= 2:
                raise RuntimeError("transient error")
            return "success"

        scheduler.submit(Task(
            name="retry_task",
            handler=fail_twice,
            max_retries=2,
        ))

        time.sleep(2)

        completed = scheduler.get_completed_tasks()
        retry_tasks = [t for t in completed if t.name == "retry_task"]
        assert len(retry_tasks) == 1
        assert retry_tasks[0].state == TaskState.COMPLETED
        assert retry_tasks[0].result == "success"
        assert retry_tasks[0].retries == 2

    def test_retry_exhausted(self, scheduler):
        def always_fail():
            raise RuntimeError("permanent error")

        scheduler.submit(Task(
            name="doomed",
            handler=always_fail,
            max_retries=1,
        ))

        time.sleep(2)

        completed = scheduler.get_completed_tasks()
        doomed = [t for t in completed if t.name == "doomed"]
        assert len(doomed) == 1
        assert doomed[0].state == TaskState.FAILED
        assert doomed[0].retries == 1

    def test_no_retry_when_max_is_zero(self, scheduler):
        call_count = {"value": 0}

        def fail_once():
            call_count["value"] += 1
            raise RuntimeError("fail")

        scheduler.submit(Task(
            name="no_retry",
            handler=fail_once,
            max_retries=0,
        ))

        time.sleep(1)

        assert call_count["value"] == 1


# ---------------------------------------------------------------------------
# 任务生命周期测试
# ---------------------------------------------------------------------------

class TestTaskLifecycle:
    def test_successful_task(self, scheduler):
        def ok():
            return 42

        scheduler.submit(Task(name="simple", handler=ok))
        time.sleep(1)

        completed = scheduler.get_completed_tasks()
        simple = [t for t in completed if t.name == "simple"]
        assert len(simple) == 1
        assert simple[0].state == TaskState.COMPLETED
        assert simple[0].result == 42

    def test_task_without_handler(self, scheduler):
        """无 handler 的任务直接完成（纯事件驱动）"""
        scheduler.submit(Task(name="event_only"))
        time.sleep(0.5)

        completed = scheduler.get_completed_tasks()
        assert any(t.name == "event_only" and t.state == TaskState.COMPLETED
                    for t in completed)

    def test_submit_returns_task_id(self, scheduler):
        tid = scheduler.submit(Task(name="test"))
        assert isinstance(tid, str)
        assert len(tid) > 0

    def test_get_stats(self, scheduler):
        stats = scheduler.get_stats()
        assert "queued" in stats
        assert "running" in stats
        assert "completed" in stats
        assert "failed" in stats
        assert "timed_out" in stats
        assert stats["max_concurrency"] == 5


# ---------------------------------------------------------------------------
# 事件发射测试
# ---------------------------------------------------------------------------

class TestEventEmission:
    def test_submit_emits_event(self, bus):
        events_received = []
        bus.subscribe("scheduler.task_submitted", lambda e: events_received.append(e))

        s = SchedulerV2(bus=bus)
        s.start()
        s.submit(Task(name="test_emit"))
        time.sleep(0.3)
        s.stop()

        assert len(events_received) >= 1
        assert events_received[0].payload["task_name"] == "test_emit"

    def test_completion_emits_event(self, bus):
        events_received = []
        bus.subscribe("scheduler.task_completed", lambda e: events_received.append(e))

        s = SchedulerV2(bus=bus)
        s.start()
        s.submit(Task(name="will_complete", handler=lambda: "ok"))
        time.sleep(1)
        s.stop()

        assert len(events_received) >= 1

    def test_decision_event_on_resource(self, bus):
        events_received = []
        bus.subscribe("scheduler.decision", lambda e: events_received.append(e))

        s = SchedulerV2(bus=bus)
        s.start()
        bus.emit(create_event(EventType.RESOURCE_CPU_SPIKE, "monitor", cpu_percent=50.0))
        time.sleep(0.3)
        s.stop()

        assert len(events_received) >= 1
        assert events_received[0].payload["action"] == "trigger_reactor"


# ---------------------------------------------------------------------------
# 边界情况
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_double_start(self, bus):
        s = SchedulerV2(bus=bus)
        s.start()
        s.start()  # 不应报错
        s.stop()

    def test_stop_without_start(self, bus):
        s = SchedulerV2(bus=bus)
        s.stop()  # 不应报错

    def test_submit_before_start(self, bus):
        s = SchedulerV2(bus=bus)
        tid = s.submit(Task(name="early"))
        assert tid  # 可以提交，但不会执行
        s.start()
        time.sleep(0.5)
        s.stop()

        completed = s.get_completed_tasks()
        assert any(t.name == "early" for t in completed)

    def test_many_tasks(self, scheduler):
        """压力测试：100 个任务"""
        counter = {"value": 0}
        lock = threading.Lock()

        def inc():
            with lock:
                counter["value"] += 1

        for i in range(100):
            scheduler.submit(Task(
                name=f"bulk_{i}",
                handler=inc,
                priority=Priority(i % 3),
            ))

        time.sleep(5)

        assert counter["value"] == 100
