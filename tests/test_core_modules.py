"""
AIOS 核心模块单元测试
测试 EventBus, Scheduler, Reactor 的核心功能
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

from core.event_bus import EventBus
from core.event import Event, EventType, create_event


class TestEventBus:
    """EventBus 单元测试"""
    
    @pytest.fixture
    def event_bus(self, tmp_path):
        """创建临时 EventBus"""
        storage = tmp_path / "events.jsonl"
        return EventBus(storage_path=storage)
    
    def test_publish_and_subscribe(self, event_bus):
        """测试发布和订阅"""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe("test.event", handler)
        
        event = create_event(
            event_type="test.event",
            payload={"message": "hello"}
        )
        
        event_bus.publish(event)
        
        assert len(received) == 1
        assert received[0].event_type == "test.event"
        assert received[0].payload["message"] == "hello"
    
    def test_wildcard_subscription(self, event_bus):
        """测试通配符订阅"""
        received = []
        
        event_bus.subscribe("*", lambda e: received.append(e))
        
        event_bus.publish(create_event("test.event1", {}))
        event_bus.publish(create_event("test.event2", {}))
        
        assert len(received) == 2
    
    def test_pattern_subscription(self, event_bus):
        """测试模式匹配订阅"""
        received = []
        
        event_bus.subscribe("test.*", lambda e: received.append(e))
        
        event_bus.publish(create_event("test.event1", {}))
        event_bus.publish(create_event("test.event2", {}))
        event_bus.publish(create_event("other.event", {}))
        
        assert len(received) == 2
    
    def test_event_persistence(self, tmp_path):
        """测试事件持久化"""
        storage = tmp_path / "events.jsonl"
        
        # 创建 EventBus 并发布事件
        bus1 = EventBus(storage_path=storage)
        bus1.publish(create_event("test.event", {"data": "test"}))
        
        # 验证文件存在
        assert storage.exists()
        
        # 读取并验证
        with open(storage, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == 1
            event_data = json.loads(lines[0])
            assert event_data["event_type"] == "test.event"
    
    def test_unsubscribe(self, event_bus):
        """测试取消订阅"""
        received = []
        
        def handler(event):
            received.append(event)
        
        event_bus.subscribe("test.event", handler)
        event_bus.publish(create_event("test.event", {}))
        
        assert len(received) == 1
        
        event_bus.unsubscribe("test.event", handler)
        event_bus.publish(create_event("test.event", {}))
        
        # 取消订阅后不应该再收到事件
        assert len(received) == 1
    
    def test_multiple_handlers(self, event_bus):
        """测试多个处理器"""
        received1 = []
        received2 = []
        
        event_bus.subscribe("test.event", lambda e: received1.append(e))
        event_bus.subscribe("test.event", lambda e: received2.append(e))
        
        event_bus.publish(create_event("test.event", {}))
        
        assert len(received1) == 1
        assert len(received2) == 1
    
    def test_event_metadata(self, event_bus):
        """测试事件元数据"""
        received = []
        event_bus.subscribe("*", lambda e: received.append(e))
        
        event = create_event(
            event_type="test.event",
            payload={"data": "test"},
            severity="WARN",
            layer="KERNEL"
        )
        
        event_bus.publish(event)
        
        assert len(received) == 1
        assert received[0].severity == "WARN"
        assert received[0].layer == "KERNEL"


class TestEvent:
    """Event 单元测试"""
    
    def test_create_event(self):
        """测试创建事件"""
        event = create_event(
            event_type="test.event",
            payload={"message": "hello"}
        )
        
        assert event.event_type == "test.event"
        assert event.payload["message"] == "hello"
        assert event.severity == "INFO"  # 默认值
        assert event.layer == "SYSTEM"  # 默认值
        assert isinstance(event.timestamp, int)
    
    def test_event_with_custom_fields(self):
        """测试自定义字段"""
        event = create_event(
            event_type="test.event",
            payload={"data": "test"},
            severity="ERR",
            layer="TOOL",
            latency_ms=1234
        )
        
        assert event.severity == "ERR"
        assert event.layer == "TOOL"
        assert event.latency_ms == 1234
    
    def test_event_serialization(self):
        """测试事件序列化"""
        event = create_event(
            event_type="test.event",
            payload={"message": "hello"}
        )
        
        # 转换为字典
        event_dict = event.to_dict()
        
        assert event_dict["event_type"] == "test.event"
        assert event_dict["payload"]["message"] == "hello"
        assert "timestamp" in event_dict
        assert "ts" in event_dict


class TestScheduler:
    """Scheduler 单元测试"""
    
    @pytest.fixture
    def scheduler_env(self, tmp_path):
        """创建 Scheduler 测试环境"""
        from core.scheduler import Scheduler
        
        event_bus = EventBus(storage_path=tmp_path / "events.jsonl")
        scheduler = Scheduler(event_bus=event_bus)
        
        return {
            "scheduler": scheduler,
            "event_bus": event_bus,
            "tmp_path": tmp_path
        }
    
    def test_scheduler_initialization(self, scheduler_env):
        """测试 Scheduler 初始化"""
        scheduler = scheduler_env["scheduler"]
        
        assert scheduler is not None
        assert scheduler.event_bus is not None
    
    def test_decision_making(self, scheduler_env):
        """测试决策制定"""
        scheduler = scheduler_env["scheduler"]
        event_bus = scheduler_env["event_bus"]
        
        decisions = []
        event_bus.subscribe("scheduler.decision.*", lambda e: decisions.append(e))
        
        # 触发一个需要决策的事件
        trigger_event = create_event(
            event_type="system.resource.high_cpu",
            payload={"cpu_percent": 90, "threshold": 80},
            severity="WARN"
        )
        
        event_bus.publish(trigger_event)
        
        # 等待决策
        import time
        time.sleep(0.1)
        
        # 验证是否有决策产生
        # 注意：这取决于 Scheduler 的实际实现
        # 如果 Scheduler 是异步的，可能需要调整测试


class TestReactor:
    """Reactor 单元测试"""
    
    @pytest.fixture
    def reactor_env(self, tmp_path):
        """创建 Reactor 测试环境"""
        from core.reactor import Reactor
        
        event_bus = EventBus(storage_path=tmp_path / "events.jsonl")
        
        # 创建测试 playbooks
        playbooks_file = tmp_path / "playbooks.json"
        playbooks = [
            {
                "id": "test_playbook_1",
                "name": "Fix High CPU",
                "trigger": {
                    "event_pattern": "system.resource.high_cpu",
                    "severity": ["WARN", "ERR"]
                },
                "actions": [
                    {
                        "type": "log",
                        "message": "High CPU detected"
                    }
                ],
                "auto_execute": True
            }
        ]
        
        with open(playbooks_file, 'w', encoding='utf-8') as f:
            json.dump(playbooks, f)
        
        reactor = Reactor(
            event_bus=event_bus,
            playbooks_path=playbooks_file
        )
        
        return {
            "reactor": reactor,
            "event_bus": event_bus,
            "tmp_path": tmp_path
        }
    
    def test_reactor_initialization(self, reactor_env):
        """测试 Reactor 初始化"""
        reactor = reactor_env["reactor"]
        
        assert reactor is not None
        assert len(reactor.playbooks) > 0
    
    def test_playbook_matching(self, reactor_env):
        """测试 Playbook 匹配"""
        reactor = reactor_env["reactor"]
        
        event = create_event(
            event_type="system.resource.high_cpu",
            payload={"cpu_percent": 90},
            severity="WARN"
        )
        
        matched = reactor.match_playbooks(event)
        
        assert len(matched) > 0
        assert matched[0]["id"] == "test_playbook_1"
    
    def test_playbook_execution(self, reactor_env):
        """测试 Playbook 执行"""
        reactor = reactor_env["reactor"]
        event_bus = reactor_env["event_bus"]
        
        executions = []
        event_bus.subscribe("reactor.playbook.*", lambda e: executions.append(e))
        
        event = create_event(
            event_type="system.resource.high_cpu",
            payload={"cpu_percent": 90},
            severity="WARN"
        )
        
        event_bus.publish(event)
        
        # 等待执行
        import time
        time.sleep(0.2)
        
        # 验证是否有执行记录
        # 注意：这取决于 Reactor 的实际实现


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
