"""
E2E: 完整工作流（submit → route → generate_spawn_commands）
对口真实 API: task_router.TaskRouter + task_executor
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

AGENT_SYS = Path(__file__).resolve().parent.parent.parent / "agent_system"
sys.path.insert(0, str(AGENT_SYS))

from task_router import TaskRouter
import task_executor


@pytest.fixture
def router(tmp_path):
    """TaskRouter with real unified_registry.json"""
    # 使用真实 registry
    from pathlib import Path as P
    real_registry = P(AGENT_SYS) / "unified_registry.json"
    real_stats = P(AGENT_SYS) / "router_stats.json"
    queue = tmp_path / "task_queue.jsonl"
    queue.write_text("", encoding="utf-8")

    with patch("task_router.QUEUE_PATH", queue), \
         patch("task_router.ROUTE_LOG_PATH", tmp_path / "route_log.jsonl"), \
         patch("task_router.STATS_PATH", tmp_path / "router_stats.json"):
        yield TaskRouter()


@pytest.mark.e2e
def test_submit_then_route_code_task(router, tmp_path):
    """submit 写入队列，route 返回正确 agent"""
    task = router.submit("实现一个 Python 排序函数", priority="normal")
    assert task.id
    assert task.status == "pending"

    route = router.route("实现一个 Python 排序函数")
    assert route.agent_id  # 有 agent
    assert route.task_type in ("code", "debug", "refactor", "test")
    assert route.confidence > 0


@pytest.mark.e2e
def test_submit_then_route_monitor_task(router, tmp_path):
    """监控任务路由到 monitor agent"""
    task = router.submit("检查 API 监控状态", priority="high")
    assert task.priority == "high"

    route = router.route("检查 API 监控状态")
    assert route.task_type in ("monitor", "health-check", "alert")


@pytest.mark.e2e
def test_submit_to_spawn_pipeline(router, tmp_path):
    """完整链路：submit → get_pending → generate_spawn_commands"""
    queue_path = tmp_path / "task_queue.jsonl"

    # submit 写入队列
    with patch("task_router.QUEUE_PATH", queue_path):
        r = TaskRouter()
        task = r.submit("写一个 hello world 脚本", priority="normal")

    # 手动改状态为 running（模拟 heartbeat 分发）
    lines = queue_path.read_text(encoding="utf-8").strip().split("\n")
    updated = []
    for line in lines:
        if line.strip():
            t = json.loads(line)
            if t["id"] == task.id:
                t["status"] = "running"
            updated.append(json.dumps(t, ensure_ascii=False))
    queue_path.write_text("\n".join(updated) + "\n", encoding="utf-8")

    # get_pending 读取
    with patch.object(task_executor, "QUEUE_PATH", queue_path):
        pending = task_executor.get_pending_tasks()

    assert len(pending) >= 1
    assert pending[0]["status"] == "running"

    # generate_spawn_commands 生成 spawn 指令
    with patch.object(task_executor, "build_memory_context",
                      return_value={"memory_hints": [], "latency_ms": 0, "error": None}):
        commands = task_executor.generate_spawn_commands(pending)

    assert len(commands) >= 1
    cmd = commands[0]
    assert "task_id" in cmd
    assert "spawn" in cmd
    assert cmd["spawn"]["task"]  # prompt 非空


@pytest.mark.e2e
def test_failed_task_not_in_pending_after_dispatch(router, tmp_path):
    """mark_tasks_dispatched 后任务不再出现在 pending 列表"""
    queue_path = tmp_path / "task_queue.jsonl"

    with patch("task_router.QUEUE_PATH", queue_path):
        r = TaskRouter()
        task = r.submit("测试幂等性", priority="normal")

    # 手动改状态为 running
    lines = queue_path.read_text(encoding="utf-8").strip().split("\n")
    updated = []
    for line in lines:
        if line.strip():
            t = json.loads(line)
            if t["id"] == task.id:
                t["status"] = "running"
            updated.append(json.dumps(t, ensure_ascii=False))
    queue_path.write_text("\n".join(updated) + "\n", encoding="utf-8")

    with patch.object(task_executor, "QUEUE_PATH", queue_path):
        pending_before = task_executor.get_pending_tasks()
        assert any(t["id"] == task.id for t in pending_before)

        task_executor.mark_tasks_dispatched([task.id])
        pending_after = task_executor.get_pending_tasks()

    assert not any(t["id"] == task.id for t in pending_after)
