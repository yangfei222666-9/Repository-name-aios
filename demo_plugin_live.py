# aios/demo_plugin_live.py - 插件系统实时演示
import sys
from pathlib import Path
import time
import random

# 设置 UTF-8 输出
sys.stdout.reconfigure(encoding="utf-8")

AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus


def demo_live():
    """实时演示插件系统"""
    print("=" * 70)
    print("AIOS 插件系统 - 实时演示")
    print("=" * 70)

    manager = get_manager()
    bus = get_bus()

    # 1. 加载插件
    print("\n【1】加载插件...")
    for name in [
        "builtin/sensor_resource",
        "builtin/notifier_console",
        "builtin/reactor_demo",
    ]:
        manager.load(name)
        print(f"  ✓ {name}")

    print(f"\n【2】事件订阅: {len(bus._subs)} 个")
    for sub in bus._subs:
        print(f"  - {sub.plugin_name}: {sub.pattern}")

    print("\n【3】开始发布事件（每3秒一次，Ctrl+C 停止）")
    print("=" * 70)

    # 模拟事件场景
    scenarios = [
        # 场景1：资源监控
        {
            "topic": "event.kernel.resource_snapshot",
            "event": {
                "type": "resource_snapshot",
                "cpu": random.uniform(30, 90),
                "mem": random.uniform(40, 85),
                "disk": random.uniform(50, 70),
            },
            "desc": "📊 资源快照",
        },
        # 场景2：Provider 错误
        {
            "topic": "event.provider.error",
            "event": {
                "type": "provider_error",
                "provider": random.choice(["openai", "anthropic", "google"]),
                "error": random.choice(["rate_limit", "timeout", "auth_failed"]),
                "category": "resource_error",
                "severity": "error",
                "data": {"error": "API 调用失败"},
            },
            "desc": "❌ Provider 错误",
        },
        # 场景3：系统告警
        {
            "topic": "alert.high_cpu",
            "event": {
                "type": "alert",
                "message": f"CPU 使用率过高: {random.randint(85, 99)}%",
                "severity": "warn",
            },
            "desc": "⚠️ 系统告警",
        },
        # 场景4：任务失败
        {
            "topic": "event.task.failed",
            "event": {
                "type": "task_failed",
                "task": random.choice(["backup", "sync", "cleanup"]),
                "error": "执行超时",
                "severity": "error",
            },
            "desc": "💥 任务失败",
        },
        # 场景5：网络错误
        {
            "topic": "event.network.error",
            "event": {
                "type": "network_error",
                "error": "连接超时",
                "severity": "error",
            },
            "desc": "🌐 网络错误",
        },
    ]

    try:
        count = 0
        while True:
            count += 1
            scenario = random.choice(scenarios)

            print(f"\n[{count}] {scenario['desc']}")
            print(f"    Topic: {scenario['topic']}")
            print(f"    Event: {scenario['event']}")

            bus.publish(scenario["topic"], scenario["event"])

            # 显示插件统计
            print(f"\n    插件统计:")
            for name, stats in manager.plugin_stats.items():
                short_name = name.split("/")[-1]
                print(
                    f"      {short_name}: {stats['calls']} 次, {stats['ok']} 成功, {stats['fail']} 失败, {stats['avg_ms']:.2f}ms"
                )

            time.sleep(3)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("演示结束！")
        print("=" * 70)

        # 最终统计
        print("\n【最终统计】")
        print(f"  总事件数: {count}")
        print(f"  插件统计:")
        for name, stats in manager.plugin_stats.items():
            print(f"    {name}:")
            print(
                f"      调用: {stats['calls']}, 成功: {stats['ok']}, 失败: {stats['fail']}"
            )
            print(f"      平均耗时: {stats['avg_ms']:.2f}ms")
            if stats["last_err"]:
                print(f"      最近错误: {stats['last_err']}")

        # 健康检查
        print("\n【健康检查】")
        results = manager.health_check_all()
        for name, health in results.items():
            status = health.get("status", "unknown")
            icon = {"ok": "✓", "warn": "⚠", "error": "✗"}.get(status, "?")
            print(f"  {icon} {name}: {status}")

        print("\n提示: Dashboard 正在运行，访问 http://localhost:8765 查看可视化")


if __name__ == "__main__":
    demo_live()
