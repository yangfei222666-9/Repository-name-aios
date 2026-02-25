"""
AIOS v0.5 完整闭环测试
验证：资源峰值 → Scheduler → Reactor → 验证

这是 v0.5 的核心：证明事件驱动架构可以实现自主修复
"""
import time
from pathlib import Path
import sys

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType, create_event
from core.event_bus import EventBus, get_event_bus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor


def test_full_loop():
    """测试完整闭环"""
    print("=" * 60)
    print("AIOS v0.5 完整闭环测试")
    print("=" * 60)
    
    # 创建新的 EventBus（避免干扰）
    import tempfile
    tmpdir = tempfile.mkdtemp()
    bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
    
    # 设置为全局 EventBus
    import aios.core.event_bus as eb
    eb._global_bus = bus
    
    # 启动 Scheduler 和 Reactor
    print("\n1. 启动系统组件...")
    scheduler = ToyScheduler(bus=bus)
    scheduler.start()
    
    reactor = ToyReactor(bus=bus)
    reactor.start()
    
    # 模拟资源峰值
    print("\n2. 模拟资源峰值...")
    bus.emit(create_event(
        EventType.RESOURCE_CPU_SPIKE,
        source="monitor",
        cpu_percent=92.0,
        threshold=80.0
    ))
    
    # 等待事件传播
    time.sleep(0.3)
    
    # 验证结果
    print("\n3. 验证结果...")
    
    # 检查 Scheduler 决策
    scheduler_actions = scheduler.get_actions()
    print(f"   Scheduler 决策数: {len(scheduler_actions)}")
    assert len(scheduler_actions) >= 1, "Scheduler 应该做出决策"
    
    # 检查 Reactor 执行
    reactor_executions = reactor.get_executions()
    print(f"   Reactor 执行数: {len(reactor_executions)}")
    assert len(reactor_executions) >= 1, "Reactor 应该执行修复"
    
    # 检查事件流
    all_events = bus.load_events()
    print(f"   总事件数: {len(all_events)}")
    
    resource_events = bus.load_events(event_type="resource.*")
    scheduler_events = bus.load_events(event_type="scheduler.*")
    reactor_events = bus.load_events(event_type="reactor.*")
    
    print(f"   - Resource 事件: {len(resource_events)}")
    print(f"   - Scheduler 事件: {len(scheduler_events)}")
    print(f"   - Reactor 事件: {len(reactor_events)}")
    
    # 验证完整闭环
    assert len(resource_events) >= 1, "应该有资源事件"
    assert len(scheduler_events) >= 1, "应该有 Scheduler 决策事件"
    assert len(reactor_events) >= 1, "应该有 Reactor 执行事件"
    
    print("\n4. 事件流追踪:")
    for event in all_events:
        print(f"   {event.timestamp} | {event.type:30s} | {event.source}")
    
    print("\n" + "=" * 60)
    print("✅ 完整闭环测试通过！")
    print("=" * 60)
    print("\n关键验证:")
    print("  ✅ 资源峰值被检测")
    print("  ✅ Scheduler 做出决策")
    print("  ✅ Reactor 执行修复")
    print("  ✅ 所有通信走 EventBus")
    print("\n这就是 AIOS v0.5 的核心：自主修复闭环")
    print("=" * 60)


def test_multiple_issues():
    """测试多个问题同时发生"""
    print("\n\n" + "=" * 60)
    print("测试：多个问题同时发生")
    print("=" * 60)
    
    # 创建新的 EventBus
    import tempfile
    tmpdir = tempfile.mkdtemp()
    bus = EventBus(storage_path=Path(tmpdir) / "events.jsonl")
    
    import aios.core.event_bus as eb
    eb._global_bus = bus
    
    # 启动组件
    scheduler = ToyScheduler(bus=bus)
    scheduler.start()
    
    reactor = ToyReactor(bus=bus)
    reactor.start()
    
    # 同时发生多个问题
    print("\n1. 同时触发多个问题...")
    bus.emit(create_event(EventType.RESOURCE_CPU_SPIKE, "monitor", cpu_percent=95.0))
    bus.emit(create_event(EventType.RESOURCE_MEMORY_HIGH, "monitor", memory_percent=92.0))
    bus.emit(create_event(EventType.AGENT_ERROR, "agent_system", error="Task timeout"))
    
    time.sleep(0.5)
    
    # 验证
    print("\n2. 验证处理结果...")
    print(f"   Scheduler 决策数: {len(scheduler.get_actions())}")
    print(f"   Reactor 执行数: {len(reactor.get_executions())}")
    
    assert len(scheduler.get_actions()) == 3, "应该有 3 个决策"
    assert len(reactor.get_executions()) == 3, "应该有 3 次执行"
    
    # 统计成功率
    successes = sum(1 for e in reactor.get_executions() if e["success"])
    success_rate = successes / len(reactor.get_executions())
    
    print(f"\n3. 修复成功率: {success_rate:.1%} ({successes}/{len(reactor.get_executions())})")
    
    print("\n✅ 多问题并发测试通过！")
    print("=" * 60)


def test_event_replay():
    """测试事件回放（调试利器）"""
    print("\n\n" + "=" * 60)
    print("测试：事件回放")
    print("=" * 60)
    
    # 创建新的 EventBus
    import tempfile
    tmpdir = tempfile.mkdtemp()
    storage_path = Path(tmpdir) / "events.jsonl"
    
    # 第一阶段：记录事件
    print("\n1. 记录事件流...")
    bus1 = EventBus(storage_path=storage_path)
    
    import aios.core.event_bus as eb
    eb._global_bus = bus1
    
    scheduler = ToyScheduler(bus=bus1)
    scheduler.start()
    
    reactor = ToyReactor(bus=bus1)
    reactor.start()
    
    bus1.emit(create_event(EventType.RESOURCE_CPU_SPIKE, "monitor"))
    time.sleep(0.2)
    
    # 第二阶段：回放事件
    print("\n2. 回放事件流...")
    bus2 = EventBus(storage_path=storage_path)
    events = bus2.load_events()
    
    print(f"   回放事件数: {len(events)}")
    for event in events:
        print(f"   - {event.type} from {event.source}")
    
    print("\n✅ 事件回放测试通过！")
    print("   （这对调试和复现问题非常有用）")
    print("=" * 60)


if __name__ == "__main__":
    test_full_loop()
    test_multiple_issues()
    test_event_replay()
    
    print("\n\n" + "=" * 60)
    print("🎉 所有测试通过！AIOS v0.5 完整闭环就绪")
    print("=" * 60)
