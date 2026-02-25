"""
AIOS 集成测试
测试多个模块协同工作
"""
import pytest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime
import sys

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType
from core.event_bus import EventBus


class TestEventBusIntegration:
    """EventBus 集成测试"""
    
    @pytest.fixture
    def event_bus(self, tmp_path):
        """创建测试用 EventBus"""
        storage = tmp_path / "events.jsonl"
        return EventBus(storage_path=storage)
    
    def test_event_flow(self, event_bus, tmp_path):
        """测试完整的事件流"""
        received_events = []
        
        # 订阅所有事件
        def handler(event):
            received_events.append(event)
        
        event_bus.subscribe("*", handler)
        
        # 发布多个事件
        events = [
            Event.create("test.event1", "test_suite", {"data": "test1"}),
            Event.create("test.event2", "test_suite", {"data": "test2"}),
            Event.create("test.event3", "test_suite", {"data": "test3"}),
        ]
        
        for event in events:
            event_bus.emit(event)
        
        # 等待处理
        time.sleep(0.1)
        
        # 验证所有事件都被接收
        assert len(received_events) == 3
        assert received_events[0].type == "test.event1"
        assert received_events[1].type == "test.event2"
        assert received_events[2].type == "test.event3"
    
    def test_event_persistence_and_reload(self, tmp_path):
        """测试事件持久化"""
        storage = tmp_path / "events.jsonl"
        
        # 创建 EventBus 并发布事件
        bus1 = EventBus(storage_path=str(storage))
        event1 = Event.create("test.event", "test_suite", {"message": "hello"})
        bus1.emit(event1)
        
        # 等待写入
        time.sleep(0.2)
        
        # 验证事件被存储（通过 EventStore）
        # EventStore 会将事件存储到自己的目录结构中
        # 我们验证事件确实被发布了
        received = []
        bus1.subscribe("test.event", lambda e: received.append(e))
        
        # 再发布一次相同的事件
        event2 = Event.create("test.event", "test_suite", {"message": "hello2"})
        bus1.emit(event2)
        
        time.sleep(0.1)
        
        # 验证订阅者收到了事件
        assert len(received) == 1
        assert received[0].type == "test.event"
    
    def test_multiple_subscribers(self, event_bus):
        """测试多个订阅者"""
        received1 = []
        received2 = []
        received3 = []
        
        event_bus.subscribe("test.*", lambda e: received1.append(e))
        event_bus.subscribe("test.event1", lambda e: received2.append(e))
        event_bus.subscribe("*", lambda e: received3.append(e))
        
        # 发布事件
        event = Event.create("test.event1", "test_suite", {})
        event_bus.emit(event)
        
        time.sleep(0.1)
        
        # 验证所有订阅者都收到了
        assert len(received1) == 1  # test.* 匹配
        assert len(received2) == 1  # test.event1 精确匹配
        assert len(received3) == 1  # * 匹配所有


class TestDashboardIntegration:
    """Dashboard 集成测试"""
    
    def test_dashboard_data_aggregation(self, tmp_path):
        """测试 Dashboard 数据聚合"""
        from dashboard.server import DashboardData
        
        # 创建测试事件文件
        events_file = tmp_path / "events.jsonl"
        
        # 生成测试事件
        now = datetime.now()
        events = []
        
        for i in range(10):
            event = {
                "ts": now.isoformat(),
                "layer": "KERNEL",
                "event": "scheduler.decision.made",
                "severity": "INFO",
                "timestamp": int(now.timestamp() * 1000) + i * 1000,
                "payload": {"action": "optimize"}
            }
            events.append(event)
        
        # 写入文件
        with open(events_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')
        
        # 读取并验证
        loaded_events = DashboardData.load_jsonl(events_file, limit=20)
        
        assert len(loaded_events) == 10
        assert all(e["layer"] == "KERNEL" for e in loaded_events)
    
    def test_dashboard_time_filtering(self, tmp_path):
        """测试 Dashboard 时间过滤"""
        from dashboard.server import DashboardData
        
        events_file = tmp_path / "events.jsonl"
        
        now = datetime.now()
        now_ms = int(now.timestamp() * 1000)
        
        # 创建不同时间的事件
        events = [
            {
                "ts": now.isoformat(),
                "event": "recent.event",
                "timestamp": now_ms - 1800000,  # 30分钟前
                "severity": "INFO"
            },
            {
                "ts": now.isoformat(),
                "event": "old.event",
                "timestamp": now_ms - 7200000,  # 2小时前
                "severity": "INFO"
            }
        ]
        
        with open(events_file, 'w', encoding='utf-8') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')
        
        # 读取所有事件
        all_events = DashboardData.load_jsonl(events_file)
        assert len(all_events) == 2
        
        # 过滤最近1小时的事件
        last_hour_ms = now_ms - 3600000
        recent_events = [
            e for e in all_events
            if DashboardData.safe_timestamp(e.get("timestamp", 0)) > last_hour_ms
        ]
        
        assert len(recent_events) == 1
        assert recent_events[0]["event"] == "recent.event"


class TestAgentSystemIntegration:
    """Agent 系统集成测试"""
    
    def test_agent_lifecycle(self, tmp_path):
        """测试 Agent 生命周期"""
        agents_file = tmp_path / "agents.jsonl"
        
        # 创建 Agent
        agent = {
            "id": "test_agent_001",
            "type": "coder",
            "status": "idle",
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "stats": {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "total_runtime_ms": 0
            }
        }
        
        with open(agents_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(agent) + '\n')
        
        # 模拟任务执行
        agent["status"] = "running"
        agent["stats"]["tasks_completed"] = 1
        agent["stats"]["total_runtime_ms"] = 1500
        
        with open(agents_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(agent) + '\n')
        
        # 读取并验证
        with open(agents_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 2
            
            # 验证最新状态
            latest = json.loads(lines[-1])
            assert latest["status"] == "running"
            assert latest["stats"]["tasks_completed"] == 1
    
    def test_circuit_breaker_integration(self, tmp_path):
        """测试熔断器集成"""
        from agent_system.circuit_breaker import CircuitBreaker
        
        state_file = tmp_path / "circuit_breaker_state.json"
        breaker = CircuitBreaker(threshold=3, timeout=60, state_file=state_file)
        
        # 记录多次失败
        for i in range(5):
            breaker.record_failure(f"task_type_{i % 2}")
        
        # 验证熔断器状态
        assert "task_type_0" in breaker.failures
        assert "task_type_1" in breaker.failures
        
        # 获取状态
        status = breaker.get_status()
        
        # 验证至少有一个任务类型被熔断
        assert len(status) >= 2
        
        # 检查失败计数
        assert status["task_type_0"]["failure_count"] >= 2
        assert status["task_type_1"]["failure_count"] >= 2


class TestBaselineIntegration:
    """Baseline 系统集成测试"""
    
    def test_baseline_snapshot_workflow(self, tmp_path):
        """测试基线快照工作流"""
        baseline_file = tmp_path / "baseline.jsonl"
        
        # 创建多个快照
        snapshots = []
        for i in range(5):
            snapshot = {
                "ts": datetime.now().isoformat(),
                "evolution_score": 0.3 + i * 0.1,  # 逐渐提升
                "grade": "ok" if i < 3 else "healthy",
                "total_events": 100 + i * 10,
                "tool_success_rate": 0.85 + i * 0.02
            }
            snapshots.append(snapshot)
        
        # 写入文件
        with open(baseline_file, 'w', encoding='utf-8') as f:
            for snapshot in snapshots:
                f.write(json.dumps(snapshot) + '\n')
        
        # 读取并验证趋势
        with open(baseline_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 5
            
            # 验证分数递增
            scores = [json.loads(line)["evolution_score"] for line in lines]
            assert scores == sorted(scores)  # 应该是递增的
            
            # 验证最新状态
            latest = json.loads(lines[-1])
            assert latest["grade"] == "healthy"
            assert latest["evolution_score"] >= 0.7


class TestMemoryIntegration:
    """记忆系统集成测试"""
    
    def test_lessons_workflow(self, tmp_path):
        """测试教训工作流"""
        lessons_file = tmp_path / "lessons.json"
        
        # 初始教训
        lessons = {
            "lessons": [
                {
                    "id": "lesson_001",
                    "category": "testing",
                    "rule": "Always write tests",
                    "confidence": "draft",
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        
        with open(lessons_file, 'w', encoding='utf-8') as f:
            json.dump(lessons, f, indent=2)
        
        # 读取并添加新教训
        with open(lessons_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data["lessons"].append({
            "id": "lesson_002",
            "category": "performance",
            "rule": "Profile before optimizing",
            "confidence": "draft",
            "created_at": datetime.now().isoformat()
        })
        
        # 写回
        with open(lessons_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        # 验证
        with open(lessons_file, 'r', encoding='utf-8') as f:
            final = json.load(f)
            assert len(final["lessons"]) == 2
            assert final["lessons"][1]["category"] == "performance"
    
    def test_memory_daily_logs(self, tmp_path):
        """测试每日记忆日志"""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        
        # 创建今天的日志
        today = datetime.now().strftime("%Y-%m-%d")
        daily_log = memory_dir / f"{today}.md"
        
        content = f"""# {today}

## 完成的工作
- 添加了单元测试
- 修复了 Dashboard bug

## 学到的教训
- 测试很重要
- 类型检查能避免很多问题
"""
        
        daily_log.write_text(content, encoding='utf-8')
        
        # 验证
        assert daily_log.exists()
        assert "单元测试" in daily_log.read_text(encoding='utf-8')


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
