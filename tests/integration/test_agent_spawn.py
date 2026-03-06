"""
Integration: Spawn 请求生成 + 文件写入
对口真实 API: task_executor.get_pending_tasks / generate_spawn_commands
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch

AGENT_SYS = Path(__file__).resolve().parent.parent.parent / "agent_system"
sys.path.insert(0, str(AGENT_SYS))

import task_executor


@pytest.fixture
def queue_with_tasks(tmp_path):
    """写入 task_queue.jsonl，返回路径"""
    q = tmp_path / "task_queue.jsonl"
    tasks = [
        {
            "id": "t-001",
            "description": "写一个排序算法",
            "type": "code",
            "agent_id": "coder",
            "priority": "high",
            "status": "running",  # task_executor 只读 running 状态
            "created_at": "2026-03-06T10:00:00",
        },
        {
            "id": "t-002",
            "description": "检查系统健康",
            "type": "monitor",
            "agent_id": "monitor",
            "priority": "normal",
            "status": "running",
            "created_at": "2026-03-06T10:01:00",
        },
    ]
    with open(q, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return q


@pytest.mark.integration
def test_get_pending_tasks_returns_list(tmp_path, queue_with_tasks):
    with patch.object(task_executor, "QUEUE_PATH", queue_with_tasks):
        tasks = task_executor.get_pending_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) == 2


@pytest.mark.integration
def test_get_pending_tasks_only_pending(tmp_path):
    q = tmp_path / "task_queue.jsonl"
    tasks = [
        {"id": "t-a", "description": "done", "type": "code", "agent_id": "coder",
         "priority": "normal", "status": "completed", "created_at": "2026-03-06T10:00:00"},
        {"id": "t-b", "description": "running one", "type": "code", "agent_id": "coder",
         "priority": "normal", "status": "running", "created_at": "2026-03-06T10:01:00"},
    ]
    with open(q, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    with patch.object(task_executor, "QUEUE_PATH", q):
        result = task_executor.get_pending_tasks()
    assert all(t["status"] == "running" for t in result)
    assert len(result) == 1


@pytest.mark.integration
def test_generate_spawn_commands_structure(tmp_path, queue_with_tasks):
    with patch.object(task_executor, "QUEUE_PATH", queue_with_tasks):
        tasks = task_executor.get_pending_tasks()

    # memory retrieval 可能超时，patch 掉
    with patch.object(task_executor, "build_memory_context",
                      return_value={"memory_hints": [], "latency_ms": 0, "error": None}):
        commands = task_executor.generate_spawn_commands(tasks)

    assert isinstance(commands, list)
    assert len(commands) == 2
    for cmd in commands:
        assert "task_id" in cmd
        assert "agent_id" in cmd
        assert "spawn" in cmd
        assert "task" in cmd["spawn"]
        assert "runTimeoutSeconds" in cmd["spawn"]


@pytest.mark.integration
def test_mark_tasks_dispatched(tmp_path, queue_with_tasks):
    with patch.object(task_executor, "QUEUE_PATH", queue_with_tasks):
        task_executor.mark_tasks_dispatched(["t-001"])
        tasks_after = task_executor.get_pending_tasks()

    # t-001 应该已经不是 pending 了
    ids = [t["id"] for t in tasks_after]
    assert "t-001" not in ids
    assert "t-002" in ids
