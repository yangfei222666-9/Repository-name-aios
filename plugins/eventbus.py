# aios/plugins/eventbus.py - 事件总线（最小可用实现）
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, Any, List
import fnmatch
import time
import logging

logger = logging.getLogger(__name__)

Handler = Callable[[Dict[str, Any]], None]


@dataclass
class Subscription:
    """订阅"""

    pattern: str
    handler: Handler
    plugin_name: str


class EventBus:
    """事件总线（支持 topic 通配符）"""

    def __init__(self):
        self._subs: List[Subscription] = []

    def subscribe(
        self, pattern: str, handler: Handler, plugin_name: str = "unknown"
    ) -> None:
        """
        订阅事件

        Args:
            pattern: topic 模式（支持通配符，如 event.* 或 event.provider.*)
            handler: 处理函数
            plugin_name: 插件名称
        """
        self._subs.append(
            Subscription(pattern=pattern, handler=handler, plugin_name=plugin_name)
        )
        logger.info(f"插件 {plugin_name} 订阅: {pattern}")

    def unsubscribe_plugin(self, plugin_name: str) -> None:
        """
        取消插件的所有订阅

        Args:
            plugin_name: 插件名称
        """
        before = len(self._subs)
        self._subs = [s for s in self._subs if s.plugin_name != plugin_name]
        after = len(self._subs)
        if before > after:
            logger.info(f"插件 {plugin_name} 取消 {before - after} 个订阅")

    def publish(self, topic: str, event: Dict[str, Any]) -> None:
        """
        发布事件

        Args:
            topic: 事件主题（如 event.provider.error）
            event: 事件数据
        """
        # 补充元数据
        event.setdefault("ts", time.time())
        event.setdefault("topic", topic)

        # 匹配订阅
        matched = 0
        for s in list(self._subs):
            if fnmatch.fnmatch(topic, s.pattern):
                try:
                    s.handler(event)
                    matched += 1
                except Exception as e:
                    # 不让单个插件错误拖垮整个 bus
                    logger.error(
                        f"插件 {s.plugin_name} 处理事件失败: {topic} - {e}",
                        exc_info=True,
                    )

        if matched > 0:
            logger.debug(f"事件 {topic} 分发到 {matched} 个订阅者")


# 全局事件总线实例
_bus: EventBus | None = None


def get_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
