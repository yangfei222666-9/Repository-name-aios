# aios/test_eventbus.py - 测试 EventBus 集成
import sys
from pathlib import Path

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding="utf-8")

AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus


def test_eventbus():
    """测试 EventBus 集成"""
    print("=" * 60)
    print("AIOS EventBus 集成测试")
    print("=" * 60)

    manager = get_manager()
    bus = get_bus()

    # 1. 加载3个内置插件
    print("\n1. 加载插件:")
    for name in [
        "builtin/sensor_resource",
        "builtin/notifier_console",
        "builtin/reactor_demo",
    ]:
        if manager.load(name):
            print(f"  ✓ {name}")

    # 2. 查看订阅情况
    print(f"\n2. 事件订阅: {len(bus._subs)} 个")
    for sub in bus._subs:
        print(f"  - {sub.plugin_name}: {sub.pattern}")

    # 3. 发布测试事件
    print("\n3. 发布测试事件:")

    # 3.1 资源快照事件
    print("\n  [测试] 发布 event.kernel.resource_snapshot")
    bus.publish(
        "event.kernel.resource_snapshot",
        {"type": "resource_snapshot", "cpu": 45.2, "mem": 60.1},
    )

    # 3.2 Provider 错误事件
    print("\n  [测试] 发布 event.provider.error")
    bus.publish(
        "event.provider.error",
        {
            "type": "provider_error",
            "provider": "openai",
            "error": "rate_limit",
            "category": "resource_error",
            "severity": "error",
            "data": {"error": "Rate limit exceeded"},
        },
    )

    # 3.3 通用错误事件
    print("\n  [测试] 发布 event.system.error")
    bus.publish(
        "event.system.error",
        {"type": "system_error", "error": "测试错误", "severity": "error"},
    )

    # 3.4 告警事件
    print("\n  [测试] 发布 alert.high_cpu")
    bus.publish("alert.high_cpu", {"type": "alert", "message": "CPU 使用率过高"})

    # 4. 查看插件统计
    print("\n4. 插件统计:")
    for name, stats in manager.plugin_stats.items():
        print(f"  - {name}:")
        print(f"    调用: {stats['calls']}, 成功: {stats['ok']}, 失败: {stats['fail']}")
        print(f"    平均耗时: {stats['avg_ms']:.2f}ms")
        if stats["last_err"]:
            print(f"    最近错误: {stats['last_err']}")

    # 5. 健康检查
    print("\n5. 健康检查:")
    results = manager.health_check_all()
    for name, health in results.items():
        status = health.get("status", "unknown")
        icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
        print(f"  {icon} {name}: {status}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_eventbus()
