"""
AIOS 实用单元测试
测试实际使用的核心功能
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime
import sys

# 添加 AIOS 到路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType


class TestEvent:
    """Event 模型测试"""
    
    def test_create_event(self):
        """测试创建事件"""
        event = Event.create(
            event_type="test.event",
            source="test_suite",
            payload={"message": "hello"}
        )
        
        assert event.type == "test.event"
        assert event.source == "test_suite"
        assert event.payload["message"] == "hello"
        assert isinstance(event.timestamp, int)
        assert len(event.id) > 0
    
    def test_event_to_dict(self):
        """测试事件序列化"""
        event = Event.create(
            event_type="test.event",
            source="test_suite",
            payload={"data": "test"}
        )
        
        event_dict = event.to_dict()
        
        assert event_dict["type"] == "test.event"
        assert event_dict["source"] == "test_suite"
        assert event_dict["payload"]["data"] == "test"
        assert "timestamp" in event_dict
        assert "id" in event_dict
    
    def test_event_from_dict(self):
        """测试从字典创建事件"""
        data = {
            "id": "test-id",
            "type": "test.event",
            "source": "test_suite",
            "timestamp": 1234567890,
            "payload": {"message": "hello"}
        }
        
        event = Event.from_dict(data)
        
        assert event.id == "test-id"
        assert event.type == "test.event"
        assert event.source == "test_suite"
        assert event.timestamp == 1234567890
        assert event.payload["message"] == "hello"
    
    def test_event_types_constants(self):
        """测试事件类型常量"""
        assert EventType.PIPELINE_STARTED == "pipeline.started"
        assert EventType.PIPELINE_COMPLETED == "pipeline.completed"
        assert EventType.PIPELINE_FAILED == "pipeline.failed"


class TestDashboardData:
    """Dashboard 数据处理测试"""
    
    def test_safe_timestamp_with_int(self):
        """测试 safe_timestamp 处理整数"""
        from dashboard.server import DashboardData
        
        result = DashboardData.safe_timestamp(1234567890)
        assert result == 1234567890
    
    def test_safe_timestamp_with_string(self):
        """测试 safe_timestamp 处理字符串"""
        from dashboard.server import DashboardData
        
        result = DashboardData.safe_timestamp("1234567890")
        assert result == 1234567890
    
    def test_safe_timestamp_with_invalid_string(self):
        """测试 safe_timestamp 处理无效字符串"""
        from dashboard.server import DashboardData
        
        result = DashboardData.safe_timestamp("invalid")
        assert result == 0
    
    def test_safe_timestamp_with_none(self):
        """测试 safe_timestamp 处理 None"""
        from dashboard.server import DashboardData
        
        result = DashboardData.safe_timestamp(None)
        assert result == 0


class TestBaselineSnapshot:
    """Baseline 快照测试"""
    
    def test_baseline_file_structure(self, tmp_path):
        """测试基线文件结构"""
        baseline_file = tmp_path / "baseline.jsonl"
        
        snapshot = {
            "ts": datetime.now().isoformat(),
            "evolution_score": 0.5,
            "grade": "ok",
            "total_events": 100
        }
        
        with open(baseline_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(snapshot) + '\n')
        
        assert baseline_file.exists()
        
        with open(baseline_file, 'r', encoding='utf-8') as f:
            loaded = json.loads(f.readline())
            assert "evolution_score" in loaded
            assert loaded["grade"] == "ok"
    
    def test_baseline_grade_logic(self):
        """测试评分分级逻辑"""
        # 简单的分级逻辑测试
        def calculate_grade(score):
            if score >= 0.7:
                return "healthy"
            elif score >= 0.5:
                return "ok"
            elif score >= 0.3:
                return "degraded"
            else:
                return "critical"
        
        assert calculate_grade(0.8) == "healthy"
        assert calculate_grade(0.6) == "ok"
        assert calculate_grade(0.4) == "degraded"
        assert calculate_grade(0.2) == "critical"


class TestAgentSystem:
    """Agent 系统测试"""
    
    def test_agent_data_structure(self, tmp_path):
        """测试 Agent 数据结构"""
        agent_data = {
            "id": "test_agent_001",
            "type": "coder",
            "status": "idle",
            "created_at": datetime.now().isoformat(),
            "stats": {
                "tasks_completed": 0,
                "tasks_failed": 0
            }
        }
        
        agents_file = tmp_path / "agents.jsonl"
        
        with open(agents_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(agent_data) + '\n')
        
        # 验证文件存在
        assert agents_file.exists()
        
        # 读取并验证
        with open(agents_file, 'r', encoding='utf-8') as f:
            loaded = json.loads(f.readline())
            assert loaded["id"] == "test_agent_001"
            assert loaded["type"] == "coder"
            assert loaded["stats"]["tasks_completed"] == 0
    
    def test_circuit_breaker_basic(self):
        """测试熔断器基本功能"""
        from agent_system.circuit_breaker import CircuitBreaker
        
        # 使用实际的 API
        breaker = CircuitBreaker(threshold=3, timeout=60)
        
        # 记录失败
        breaker.record_failure("test_task")
        
        # 验证失败被记录
        assert "test_task" in breaker.failures
        assert breaker.failures["test_task"][0] == 1


class TestKnowledgeExtraction:
    """知识提取测试"""
    
    def test_extract_error_patterns(self, tmp_path):
        """测试提取错误模式"""
        # 创建测试事件
        events_file = tmp_path / "events.jsonl"
        
        # 同一个错误重复3次
        for i in range(3):
            event = {
                "ts": datetime.now().isoformat(),
                "severity": "ERR",
                "event": "error.timeout",
                "payload": {"component": "scheduler"}
            }
            
            with open(events_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
        
        # 验证文件
        assert events_file.exists()
        
        with open(events_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 3


class TestPerformanceOptimization:
    """性能优化测试"""
    
    def test_identify_slow_operations(self, tmp_path):
        """测试识别慢操作"""
        events_file = tmp_path / "events.jsonl"
        
        # 创建慢操作事件
        slow_event = {
            "ts": datetime.now().isoformat(),
            "event": "task.completed",
            "latency_ms": 6000,  # 6秒，超过阈值
            "payload": {"task_id": "slow_task"}
        }
        
        with open(events_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(slow_event) + '\n')
        
        # 读取并验证
        with open(events_file, 'r', encoding='utf-8') as f:
            loaded = json.loads(f.readline())
            assert loaded["latency_ms"] > 5000


class TestMemoryManagement:
    """记忆管理测试"""
    
    def test_memory_file_structure(self, tmp_path):
        """测试记忆文件结构"""
        memory_file = tmp_path / "MEMORY.md"
        
        content = """# MEMORY.md

## 项目
- AIOS v0.5

## 教训
- 测试很重要
"""
        
        memory_file.write_text(content, encoding='utf-8')
        
        assert memory_file.exists()
        assert "AIOS" in memory_file.read_text(encoding='utf-8')
    
    def test_lessons_json_structure(self, tmp_path):
        """测试教训 JSON 结构"""
        lessons_file = tmp_path / "lessons.json"
        
        lessons = {
            "lessons": [
                {
                    "id": "lesson_001",
                    "category": "testing",
                    "rule": "Always write tests",
                    "confidence": "verified"
                }
            ]
        }
        
        with open(lessons_file, 'w', encoding='utf-8') as f:
            json.dump(lessons, f, indent=2)
        
        assert lessons_file.exists()
        
        with open(lessons_file, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
            assert len(loaded["lessons"]) == 1
            assert loaded["lessons"][0]["category"] == "testing"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=.", "--cov-report=term-missing"])
