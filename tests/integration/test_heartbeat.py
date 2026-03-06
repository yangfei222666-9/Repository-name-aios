"""
Integration: Heartbeat 流程
对口真实 API: heartbeat_v5.process_task_queue / check_system_health
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

AGENT_SYS = Path(__file__).resolve().parent.parent.parent / "agent_system"
sys.path.insert(0, str(AGENT_SYS))

import heartbeat_v5


@pytest.fixture
def empty_queue(tmp_path):
    q = tmp_path / "task_queue.jsonl"
    q.write_text("", encoding="utf-8")
    return q


@pytest.fixture
def queue_with_pending(tmp_path):
    q = tmp_path / "task_queue.jsonl"
    tasks = [
        {"id": f"t-{i:03d}", "description": f"task {i}", "type": "code",
         "agent_id": "coder", "priority": "normal", "status": "pending",
         "created_at": "2026-03-06T10:00:00"}
        for i in range(3)
    ]
    with open(q, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return q


@pytest.mark.integration
def test_process_task_queue_no_tasks(empty_queue):
    """空队列时 processed=0"""
    with patch("heartbeat_v5.list_tasks", return_value=[]):
        result = heartbeat_v5.process_task_queue(max_tasks=5)
    assert isinstance(result, dict)
    assert result["processed"] == 0


@pytest.mark.integration
def test_process_task_queue_returns_dict():
    """process_task_queue 始终返回 dict"""
    with patch("heartbeat_v5.list_tasks", return_value=[]):
        result = heartbeat_v5.process_task_queue()
    assert isinstance(result, dict)
    assert "processed" in result
    assert "success" in result
    assert "failed" in result


@pytest.mark.integration
def test_check_system_health_returns_score():
    """check_system_health 返回 score 字段"""
    mock_stats = {
        "total": 10,
        "by_status": {"completed": 8, "failed": 1, "pending": 1},
    }
    with patch("heartbeat_v5.queue_stats", return_value=mock_stats):
        result = heartbeat_v5.check_system_health()
    assert isinstance(result, dict)
    assert "score" in result
    assert 0 <= result["score"] <= 100


@pytest.mark.integration
def test_check_system_health_perfect_score():
    """全部完成时 score 应为 100"""
    mock_stats = {
        "total": 5,
        "by_status": {"completed": 5, "failed": 0, "pending": 0},
    }
    with patch("heartbeat_v5.queue_stats", return_value=mock_stats):
        result = heartbeat_v5.check_system_health()
    assert result["score"] == 100.0


@pytest.mark.integration
def test_check_system_health_empty_queue():
    """空队列时 score 应为 100（无失败）"""
    mock_stats = {
        "total": 0,
        "by_status": {"completed": 0, "failed": 0, "pending": 0},
    }
    with patch("heartbeat_v5.queue_stats", return_value=mock_stats):
        result = heartbeat_v5.check_system_health()
    assert result["score"] == 100.0


@pytest.mark.integration
def test_check_system_health_high_failure():
    """高失败率时 score 应该低"""
    mock_stats = {
        "total": 10,
        "by_status": {"completed": 2, "failed": 8, "pending": 0},
    }
    with patch("heartbeat_v5.queue_stats", return_value=mock_stats):
        result = heartbeat_v5.check_system_health()
    assert result["score"] < 50
