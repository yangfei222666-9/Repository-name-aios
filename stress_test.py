"""
AIOS v0.5 压力测试
模拟资源峰值，测试自动修复
"""
import sys
import time
from pathlib import Path

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import EventType, create_event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine

print("=" * 60)
print("AIOS v0.5 压力测试")
print("=" * 60)

# 使用持久化的 EventBus
events_file = AIOS_ROOT / "data" / "events.jsonl"
events_file.parent.mkdir(parents=True, exist_ok=True)

bus = EventBus(storage_path=events_file)

# 启动组件
print("\n1. 启动系统组件...")
scheduler = ToyScheduler(bus=bus)
scheduler.start()

reactor = ToyReactor(bus=bus)
reactor.start()

score_engine = ToyScoreEngine(bus=bus)
score_engine.start()

print("\n2. 模拟资源峰值...")

# 模拟 CPU 峰值
print("  → 触发 CPU 峰值（95%）")
bus.emit(create_event(
    EventType.RESOURCE_CPU_SPIKE,
    source="stress_test",
    cpu_percent=95.0,
    threshold=80.0
))

time.sleep(0.5)

# 模拟内存峰值
print("  → 触发内存峰值（92%）")
bus.emit(create_event(
    EventType.RESOURCE_MEMORY_HIGH,
    source="stress_test",
    memory_percent=92.0,
    threshold=85.0
))

time.sleep(0.5)

# 模拟 Agent 错误
print("  → 触发 Agent 错误")
bus.emit(create_event(
    EventType.AGENT_ERROR,
    source="stress_test",
    error="Task timeout",
    agent_id="test_agent"
))

time.sleep(0.5)

# 检查结果
print("\n3. 检查系统响应...")

print(f"\n[Scheduler]")
print(f"  决策数: {len(scheduler.get_actions())}")
for i, action in enumerate(scheduler.get_actions(), 1):
    print(f"  {i}. {action['action']}: {action['reason']}")

print(f"\n[Reactor]")
print(f"  执行数: {len(reactor.get_executions())}")
success_count = sum(1 for e in reactor.get_executions() if e['success'])
print(f"  成功率: {success_count}/{len(reactor.get_executions())}")
for i, exec in enumerate(reactor.get_executions(), 1):
    status = "✅" if exec['success'] else "❌"
    print(f"  {i}. {status} {exec['playbook']} - {exec['action']} ({exec['duration_ms']}ms)")

print(f"\n[ScoreEngine]")
print(f"  当前评分: {score_engine.get_score():.3f}")
stats = score_engine.get_stats()
print(f"  成功/失败: {stats['success_count']}/{stats['failure_count']}")
print(f"  资源告警: {stats['resource_alerts']}")

# 判断结果
print("\n" + "=" * 60)
if score_engine.get_score() < 0.5:
    print("⚠️ 系统降级")
    print(f"   Score: {score_engine.get_score():.3f}")
    print(f"   建议：检查系统资源")
elif len(reactor.get_executions()) > 0:
    print("✅ 自动修复成功")
    print(f"   Reactor 执行: {len(reactor.get_executions())} 次")
    print(f"   成功率: {success_count}/{len(reactor.get_executions())}")
else:
    print("ℹ️ 系统正常")

print("=" * 60)
