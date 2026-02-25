# aios/init_plugins.py - 初始化插件系统
"""
在 AIOS 启动时初始化插件系统

使用方法：
    from init_plugins import init_plugins
    init_plugins()
"""
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event_bus import EventBus
from plugins.bridge import init_plugin_system, get_bridge
from plugins.manager import get_manager
import logging

logger = logging.getLogger(__name__)


def init_plugins(core_bus: EventBus = None) -> None:
    """
    初始化插件系统

    Args:
        core_bus: AIOS 核心 EventBus（可选，如果不提供则创建新的）
    """
    logger.info("=" * 60)
    logger.info("初始化 AIOS 插件系统")
    logger.info("=" * 60)

    # 1. 获取或创建 EventBus
    if core_bus is None:
        from core.event_bus import EventBus

        core_bus = EventBus()
        logger.info("创建新的 EventBus")
    else:
        logger.info("使用现有 EventBus")

    # 2. 初始化插件管理器
    manager = get_manager()
    logger.info(f"插件管理器已初始化，已加载 {len(manager.plugins)} 个插件")

    # 3. 桥接到核心 EventBus
    bridge = init_plugin_system(core_bus)
    logger.info("插件系统已桥接到核心 EventBus")

    # 4. 显示已加载的插件
    if manager.plugins:
        logger.info("\n已加载的插件:")
        for name, plugin in manager.plugins.items():
            meta = plugin.meta()
            logger.info(f"  - {meta.name} v{meta.version} ({meta.plugin_type.value})")
            patterns = plugin.subscriptions()
            if patterns:
                logger.info(f"    订阅: {', '.join(patterns)}")
    else:
        logger.info("没有已加载的插件")

    logger.info("=" * 60)
    logger.info("插件系统初始化完成")
    logger.info("=" * 60)


def test_plugin_integration():
    """测试插件集成"""
    print("\n" + "=" * 60)
    print("测试插件集成")
    print("=" * 60)

    # 1. 初始化
    from core.event_bus import EventBus
    from core.event import Event

    bus = EventBus()
    init_plugins(bus)

    # 2. 加载测试插件
    manager = get_manager()
    manager.load("builtin/notifier_console")
    manager.load("builtin/reactor_demo")

    # 重新桥接（因为新加载了插件）
    bridge = get_bridge()
    bridge.bridge_eventbus(bus)

    # 3. 发布测试事件
    print("\n发布测试事件:")

    test_events = [
        Event.create(
            event_type="provider.error",
            source="test",
            payload={"provider": "openai", "error": "rate_limit", "severity": "error"},
        ),
        Event.create(
            event_type="task.failed",
            source="test",
            payload={"task": "backup", "error": "timeout", "severity": "error"},
        ),
    ]

    for event in test_events:
        print(f"  → {event.type}")
        bus.emit(event)

    # 4. 查看统计
    print("\n插件统计:")
    for name, stats in manager.plugin_stats.items():
        print(f"  {name}:")
        print(f"    调用: {stats['calls']}, 成功: {stats['ok']}, 失败: {stats['fail']}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # 运行测试
    test_plugin_integration()
