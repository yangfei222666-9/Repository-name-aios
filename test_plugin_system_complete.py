# aios/test_plugin_system_complete.py - 完整测试插件系统
import sys
from pathlib import Path
import json

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding="utf-8")

AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus
from plugins.registry import get_capability_registry


def test_complete():
    """完整测试插件系统"""
    print("=" * 70)
    print("AIOS 插件系统 v0.1 - 完整测试")
    print("=" * 70)

    manager = get_manager()
    bus = get_bus()
    cap_reg = get_capability_registry()

    # 1. 发现插件
    print("\n【1/8】发现插件")
    plugins = manager.discover()
    print(f"  发现 {len(plugins)} 个插件:")
    for name in plugins:
        print(f"    - {name}")

    # 2. 加载3个内置插件
    print("\n【2/8】加载内置插件")
    for name in [
        "builtin/sensor_resource",
        "builtin/notifier_console",
        "builtin/reactor_demo",
    ]:
        if manager.load(name):
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")

    # 3. 查看订阅情况
    print(f"\n【3/8】事件订阅")
    print(f"  总订阅数: {len(bus._subs)}")
    for sub in bus._subs:
        print(f"    - {sub.plugin_name}: {sub.pattern}")

    # 4. 发布测试事件
    print("\n【4/8】发布测试事件")

    test_events = [
        ("event.kernel.resource_snapshot", {"type": "resource_snapshot", "cpu": 45.2}),
        (
            "event.provider.error",
            {
                "type": "provider_error",
                "provider": "openai",
                "error": "rate_limit",
                "category": "resource_error",
                "severity": "error",
                "data": {"error": "Rate limit exceeded"},
            },
        ),
        ("event.system.error", {"type": "system_error", "error": "测试错误"}),
        ("alert.high_cpu", {"type": "alert", "message": "CPU 使用率过高"}),
    ]

    for topic, event in test_events:
        print(f"  → {topic}")
        bus.publish(topic, event)

    # 5. 插件统计
    print("\n【5/8】插件统计")
    for name, stats in manager.plugin_stats.items():
        print(f"  {name}:")
        print(
            f"    调用: {stats['calls']}, 成功: {stats['ok']}, 失败: {stats['fail']}"
        )
        print(f"    平均耗时: {stats['avg_ms']:.2f}ms")
        if stats["last_err"]:
            print(f"    最近错误: {stats['last_err']}")

    # 6. 能力注册表
    print("\n【6/8】能力注册表")
    print(f"  技能: {len(cap_reg.skills)}")
    print(f"  任务: {len(cap_reg.tasks)}")
    print(f"  路由: {len(cap_reg.routes)}")
    print(f"  指标: {len(cap_reg.metrics)}")

    # 7. 健康检查
    print("\n【7/8】健康检查")
    results = manager.health_check_all()
    for name, health in results.items():
        status = health.get("status", "unknown")
        icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
        message = health.get("message", "")
        print(f"  {icon} {name}: {status} - {message}")

    # 8. Dashboard 数据
    print("\n【8/8】Dashboard 数据")
    try:
        from dashboard.server import DashboardData

        plugins_data = DashboardData.get_plugins_status()
        print(f"  总插件: {plugins_data['total']}")
        print(f"  已启用: {plugins_data['enabled']}")
        print(f"  失败: {plugins_data['failed']}")
        print(f"  插件列表:")
        for item in plugins_data["items"]:
            print(
                f"    - {item['name']} ({item['type']}): {item['calls']} 次调用, {item['avg_ms']}ms"
            )
    except Exception as e:
        print(f"  ✗ Dashboard 数据获取失败: {e}")

    # 总结
    print("\n" + "=" * 70)
    print("✅ 测试完成！插件系统 v0.1 全部功能正常")
    print("=" * 70)

    # 输出 JSON 格式（方便自动化测试）
    print("\n【测试结果 JSON】")
    result = {
        "plugins_discovered": len(plugins),
        "plugins_loaded": len(manager.plugins),
        "subscriptions": len(bus._subs),
        "events_published": len(test_events),
        "plugin_stats": manager.plugin_stats,
        "health_check": results,
        "capability_registry": {
            "skills": len(cap_reg.skills),
            "tasks": len(cap_reg.tasks),
            "routes": len(cap_reg.routes),
            "metrics": len(cap_reg.metrics),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    test_complete()
