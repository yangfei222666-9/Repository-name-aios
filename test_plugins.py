# aios/test_plugins.py - 插件系统测试
import sys
from pathlib import Path

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding="utf-8")

AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager


def test_plugins():
    """测试插件系统"""
    print("=" * 60)
    print("AIOS 插件系统测试")
    print("=" * 60)

    manager = get_manager()

    # 1. 发现插件
    print("\n1. 发现插件:")
    plugins = manager.discover()
    for name in plugins:
        print(f"  - {name}")

    # 2. 加载3个内置插件
    print("\n2. 加载内置插件:")
    for name in [
        "builtin/sensor_resource",
        "builtin/notifier_console",
        "builtin/reactor_demo",
    ]:
        if manager.load(name):
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")

    # 3. 列出已加载插件
    print("\n3. 已加载插件:")
    for meta in manager.list():
        print(f"  - {meta.name} v{meta.version} ({meta.plugin_type.value})")

    # 4. 健康检查
    print("\n4. 健康检查:")
    results = manager.health_check_all()
    for name, health in results.items():
        status = health.get("status", "unknown")
        message = health.get("message", "")
        icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
        print(f"  {icon} {name}: {status} - {message}")

    # 5. 测试 Sensor 插件采集数据
    print("\n5. 测试 Sensor 插件:")
    sensor = manager.get("builtin/sensor_resource")
    if sensor:
        events = sensor.collect()
        for event in events:
            print(f"  - [{event['category']}] {event['data']}")

    # 6. 测试 Notifier 插件发送通知
    print("\n6. 测试 Notifier 插件:")
    notifier = manager.get("builtin/notifier_console")
    if notifier:
        notifier.send("这是一条测试通知", "info")
        notifier.send("这是一条警告", "warn")
        notifier.send("这是一条错误", "error")

    # 7. 测试 Reactor 插件匹配事件
    print("\n7. 测试 Reactor 插件:")
    reactor = manager.get("builtin/reactor_demo")
    if reactor:
        # 模拟一个错误事件
        test_event = {
            "timestamp": 1708761600,
            "category": "resource_error",
            "severity": "error",
            "data": {"error": "内存不足"},
        }
        if reactor.match(test_event):
            print(f"  ✓ 匹配事件: {test_event['category']}")
            action = reactor.react(test_event)
            print(f"  ✓ 生成动作: {action}")
            reactor.verify(action)
        else:
            print(f"  ✗ 未匹配事件")

    # 8. 测试能力注册表
    print("\n8. 能力注册表:")
    cap_reg = manager.capability_registry
    print(f"  - 技能: {len(cap_reg.skills)}")
    print(f"  - 任务: {len(cap_reg.tasks)}")
    print(f"  - 路由: {len(cap_reg.routes)}")
    print(f"  - 指标: {len(cap_reg.metrics)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_plugins()
