"""
EventBus v2.0 测试套件
"""
import time
import tempfile
from pathlib import Path
import sys

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType, create_event
from core.event_bus import EventBus


def test_basic_emit_and_subscribe():
    """测试基本的发布订阅"""
    print("测试 1: 基本发布订阅")
    
    # 创建临时 EventBus
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 订阅事件
        received_events = []
        def handler(event: Event):
            received_events.append(event)
        
        bus.subscribe("test.event", handler)
        
        # 发布事件
        event = create_event("test.event", "test_source", message="Hello")
        bus.emit(event)
        
        # 验证
        assert len(received_events) == 1
        assert received_events[0].type == "test.event"
        assert received_events[0].payload["message"] == "Hello"
        
        print("✅ 基本发布订阅测试通过")


def test_wildcard_subscription():
    """测试通配符订阅"""
    print("\n测试 2: 通配符订阅")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 订阅所有 agent 事件
        agent_events = []
        def agent_handler(event: Event):
            agent_events.append(event)
        
        bus.subscribe("agent.*", agent_handler)
        
        # 发布多个事件
        bus.emit(create_event(EventType.AGENT_CREATED, "test", agent_id="a1"))
        bus.emit(create_event(EventType.AGENT_ERROR, "test", error="test"))
        bus.emit(create_event(EventType.PIPELINE_STARTED, "test"))  # 不应该被捕获
        
        # 验证
        assert len(agent_events) == 2
        assert all(e.type.startswith("agent.") for e in agent_events)
        
        print("✅ 通配符订阅测试通过")


def test_event_persistence():
    """测试事件持久化"""
    print("\n测试 3: 事件持久化")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "events.jsonl"
        
        # 第一个 bus 发布事件
        bus1 = EventBus(storage_path=storage_path)
        bus1.emit(create_event("test.event", "source1", data="event1"))
        bus1.emit(create_event("test.event", "source2", data="event2"))
        
        # 第二个 bus 读取事件
        bus2 = EventBus(storage_path=storage_path)
        events = bus2.load_events()
        
        # 验证（可能包含迁移的旧事件）
        assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"
        
        # 查找我们发布的事件（最近的2个）
        test_events = [e for e in events if e.payload.get("data") in ["event1", "event2"]]
        assert len(test_events) >= 2, f"Expected at least 2 test events, got {len(test_events)}"
        
        print("✅ 事件持久化测试通过")


def test_event_filtering():
    """测试事件过滤"""
    print("\n测试 4: 事件过滤")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 发布多个事件
        now = int(time.time() * 1000)
        bus.emit(create_event(EventType.AGENT_CREATED, "test", agent_id="a1"))
        time.sleep(0.01)
        bus.emit(create_event(EventType.PIPELINE_STARTED, "test"))
        time.sleep(0.01)
        bus.emit(create_event(EventType.AGENT_ERROR, "test", error="test"))
        
        # 测试类型过滤
        agent_events = bus.load_events(event_type="agent.*")
        assert len(agent_events) >= 2, f"Expected at least 2 agent events, got {len(agent_events)}"
        
        # 测试时间过滤
        recent_events = bus.load_events(since=now + 15)
        assert len(recent_events) >= 1
        
        # 测试数量限制
        limited_events = bus.load_events(limit=2)
        assert len(limited_events) == 2
        
        print("✅ 事件过滤测试通过")


def test_multiple_subscribers():
    """测试多个订阅者"""
    print("\n测试 5: 多个订阅者")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 多个订阅者
        received1 = []
        received2 = []
        
        bus.subscribe("test.*", lambda e: received1.append(e))
        bus.subscribe("test.event", lambda e: received2.append(e))
        
        # 发布事件
        bus.emit(create_event("test.event", "test"))
        
        # 验证
        assert len(received1) == 1  # 通配符订阅者
        assert len(received2) == 1  # 精确订阅者
        
        print("✅ 多个订阅者测试通过")


def test_subscriber_error_handling():
    """测试订阅者错误处理"""
    print("\n测试 6: 订阅者错误处理")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 一个会出错的订阅者
        def bad_handler(event: Event):
            raise Exception("Intentional error")
        
        # 一个正常的订阅者
        received = []
        def good_handler(event: Event):
            received.append(event)
        
        bus.subscribe("test.event", bad_handler)
        bus.subscribe("test.event", good_handler)
        
        # 发布事件
        bus.emit(create_event("test.event", "test"))
        
        # 验证：即使一个订阅者出错，其他订阅者仍然能收到事件
        assert len(received) == 1
        
        print("✅ 订阅者错误处理测试通过")


def test_event_count():
    """测试事件统计"""
    print("\n测试 7: 事件统计")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
        
        # 发布多个事件
        bus.emit(create_event(EventType.AGENT_CREATED, "test"))
        bus.emit(create_event(EventType.AGENT_ERROR, "test"))
        bus.emit(create_event(EventType.PIPELINE_STARTED, "test"))
        
        # 统计
        total = bus.count_events()
        agent_count = bus.count_events(event_type="agent.*")
        
        assert total >= 3, f"Expected at least 3 events, got {total}"
        assert agent_count >= 2, f"Expected at least 2 agent events, got {agent_count}"
        
        print("✅ 事件统计测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("EventBus v2.0 测试套件")
    print("=" * 60)
    
    test_basic_emit_and_subscribe()
    test_wildcard_subscription()
    test_event_persistence()
    test_event_filtering()
    test_multiple_subscribers()
    test_subscriber_error_handling()
    test_event_count()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！EventBus v2.0 就绪")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
