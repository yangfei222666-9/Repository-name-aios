# aios/demo_quick.py - 快速演示
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus

print("=" * 60)
print("AIOS 插件系统 - 快速演示")
print("=" * 60)

manager = get_manager()
bus = get_bus()

# 加载插件
print("\n加载插件...")
manager.load("builtin/sensor_resource")
manager.load("builtin/notifier_console")
manager.load("builtin/reactor_demo")

print(f"\n事件订阅: {len(bus._subs)} 个")

# 发布5个测试事件
print("\n发布测试事件:")

events = [
    ("event.provider.error", {"error": "rate_limit", "category": "resource_error", "severity": "error", "data": {"error": "Rate limit"}}),
    ("alert.high_cpu", {"message": "CPU 90%"}),
    ("event.task.failed", {"task": "backup", "error": "timeout"}),
    ("event.network.error", {"error": "timeout"}),
    ("event.system.error", {"error": "test"}),
]

for i, (topic, event) in enumerate(events, 1):
    print(f"\n[{i}] {topic}")
    bus.publish(topic, event)

# 统计
print("\n" + "=" * 60)
print("插件统计:")
for name, stats in manager.plugin_stats.items():
    print(f"  {name}: {stats['calls']} 次, {stats['avg_ms']:.2f}ms")

print("\n✅ 演示完成！")
print("提示: 访问 http://localhost:8765 查看 Dashboard")
