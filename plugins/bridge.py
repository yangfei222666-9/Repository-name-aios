# aios/plugins/bridge.py - 插件系统与 AIOS 核心的桥接
"""
插件系统桥接模块

职责：
1. 将插件 EventBus 连接到 AIOS 核心 EventBus
2. 将插件注册到 Scheduler（定时触发 Sensor）
3. 将插件注册到 Reactor（自动修复）
"""
import sys
from pathlib import Path
from typing import Optional
import logging

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.event_bus import EventBus as CoreEventBus
from core.event import Event
from plugins.manager import PluginManager, get_manager
from plugins.base import SensorPlugin, ReactorPlugin, NotifierPlugin

logger = logging.getLogger(__name__)


class PluginBridge:
    """插件系统桥接器"""

    def __init__(
        self,
        core_bus: Optional[CoreEventBus] = None,
        plugin_manager: Optional[PluginManager] = None,
    ):
        """
        初始化桥接器

        Args:
            core_bus: AIOS 核心 EventBus
            plugin_manager: 插件管理器
        """
        self.core_bus = core_bus
        self.plugin_manager = plugin_manager or get_manager()
        self._bridged = False

    def bridge_eventbus(self, core_bus: CoreEventBus) -> None:
        """
        桥接 EventBus

        将插件的事件订阅连接到 AIOS 核心 EventBus

        Args:
            core_bus: AIOS 核心 EventBus
        """
        if self._bridged:
            logger.warning("EventBus 已经桥接过了")
            return

        self.core_bus = core_bus

        # 遍历所有已加载的插件
        for name, plugin in self.plugin_manager.plugins.items():
            # 获取插件订阅的 topic
            patterns = plugin.subscriptions()
            if not patterns:
                continue

            # 为每个 pattern 创建订阅
            for pattern in patterns:
                # 创建适配器：将 AIOS Event 转换为插件 dict
                def make_handler(p=plugin, pat=pattern):
                    def handler(event: Event):
                        # 转换 Event 对象为 dict
                        event_dict = {
                            "timestamp": event.timestamp,
                            "topic": event.type,
                            "type": event.type,
                            "source": event.source,
                            "data": event.payload,
                            "severity": event.payload.get("severity", "info"),
                        }
                        # 调用插件的安全处理器
                        safe_handler = self.plugin_manager._safe_handler(name, p)
                        safe_handler(event_dict)

                    return handler

                # 订阅到核心 EventBus
                # 注意：核心 EventBus 使用 event.type 作为匹配
                # 我们需要将 pattern 转换为 event.type 格式
                # 例如：event.provider.error → provider.error
                core_pattern = pattern.replace("event.", "")
                core_bus.subscribe(core_pattern, make_handler())
                logger.info(f"插件 {name} 订阅: {core_pattern} (原始: {pattern})")

        self._bridged = True
        logger.info(f"EventBus 桥接完成，已桥接 {len(self.plugin_manager.plugins)} 个插件")

    def register_sensors_to_scheduler(self) -> None:
        """
        将 Sensor 插件注册到 Scheduler

        定时触发 Sensor 插件的 collect() 方法
        """
        # TODO: 对接 Scheduler
        # 需要在 Scheduler 中添加定时任务，定期调用 sensor.collect()
        logger.info("Sensor 插件注册到 Scheduler（待实现）")

    def register_reactors(self) -> None:
        """
        将 Reactor 插件注册到 Reactor 系统

        Reactor 插件通过 EventBus 自动触发，无需额外注册
        """
        logger.info("Reactor 插件已通过 EventBus 自动注册")

    def publish_to_plugins(self, event: Event) -> None:
        """
        发布事件到插件系统

        Args:
            event: AIOS 核心事件
        """
        if not self.core_bus:
            logger.warning("EventBus 未桥接，无法发布事件")
            return

        # 事件已经通过 EventBus 订阅机制自动分发
        # 这个方法主要用于手动触发
        pass


# 全局桥接器实例
_bridge: Optional[PluginBridge] = None


def get_bridge() -> PluginBridge:
    """获取全局桥接器实例"""
    global _bridge
    if _bridge is None:
        _bridge = PluginBridge()
    return _bridge


def init_plugin_system(core_bus: CoreEventBus) -> PluginBridge:
    """
    初始化插件系统并桥接到 AIOS 核心

    Args:
        core_bus: AIOS 核心 EventBus

    Returns:
        桥接器实例
    """
    bridge = get_bridge()
    bridge.bridge_eventbus(core_bus)
    bridge.register_reactors()
    logger.info("插件系统初始化完成")
    return bridge
