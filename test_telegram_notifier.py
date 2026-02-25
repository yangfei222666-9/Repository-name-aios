# aios/test_telegram_notifier.py - 测试 Telegram Notifier
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus

print("=" * 60)
print("测试 Telegram Notifier")
print("=" * 60)

manager = get_manager()
bus = get_bus()

# 加载插件
print("\n加载插件...")
manager.load("builtin/notifier_telegram")

# 发布测试事件
print("\n发布测试事件（你会在 Telegram 收到通知）:")

test_events = [
    ("event.provider.error", {
        "provider": "openai",
        "error": "Rate limit exceeded",
        "severity": "error",
        "data": {"error": "Rate limit exceeded", "provider": "openai"}
    }),
    ("alert.high_cpu", {
        "message": "CPU 使用率过高: 95%",
        "severity": "warn"
    }),
    ("event.task.failed", {
        "task": "backup",
        "error": "timeout",
        "severity": "error",
        "data": {"task": "backup", "error": "timeout"}
    }),
]

for i, (topic, event) in enumerate(test_events, 1):
    print(f"\n[{i}] {topic}")
    bus.publish(topic, event)
    import time
    time.sleep(6)  # 等待速率限制

print("\n" + "=" * 60)
print("✅ 测试完成！请检查 Telegram")
print("=" * 60)
