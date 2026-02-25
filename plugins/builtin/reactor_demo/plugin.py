# aios/plugins/builtin/reactor_demo/plugin.py
from typing import Dict, Any
import sys
from pathlib import Path

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import ReactorPlugin, PluginMeta, PluginType


class DemoReactorPlugin(ReactorPlugin):
    """演示 Reactor 插件（收到特定错误触发 noop action）"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="reactor_demo",
            version="1.0.0",
            description="演示 Reactor 插件（自动修复示例）",
            author="小九",
            plugin_type=PluginType.REACTOR,
            capabilities=["match", "react", "verify"],
        )

    def subscriptions(self) -> list:
        """订阅 provider 错误事件"""
        return ["event.provider.error", "event.*error*"]

    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        self._target_categories = config.get(
            "target_categories", ["resource_error", "gpu_error"]
        )
        print(f"Demo Reactor 初始化成功，监听类别: {self._target_categories}")
        return True

    def match(self, event: Dict[str, Any]) -> bool:
        """
        判断是否匹配此事件

        Args:
            event: 事件字典

        Returns:
            是否匹配
        """
        category = event.get("category", "")
        severity = event.get("severity", "")

        # 匹配目标类别 + error 级别
        return category in self._target_categories and severity == "error"

    def react(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成修复动作

        Args:
            event: 事件字典

        Returns:
            动作字典
        """
        category = event.get("category", "unknown")
        data = event.get("data", {})
        error = data.get("error", "未知错误")

        print(f"🔧 Demo Reactor 触发修复: [{category}] {error}")

        # 返回一个 noop action（演示用）
        return {
            "type": "noop",
            "category": category,
            "reason": f"演示修复: {error}",
            "timestamp": event.get("timestamp"),
        }

    def verify(self, action: Dict[str, Any]) -> bool:
        """
        验证修复是否成功

        Args:
            action: 动作字典

        Returns:
            是否成功
        """
        # noop 总是成功
        print(f"✅ Demo Reactor 验证成功: {action.get('reason')}")
        return True

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "ok",
            "message": f"Demo Reactor 正常，监听 {len(self._target_categories)} 个类别",
        }

    def on_event(self, event: Dict[str, Any]) -> None:
        """监听事件，自动触发修复"""
        if self.match(event):
            action = self.react(event)
            self.verify(action)


# 导出插件类
PLUGIN_CLASS = DemoReactorPlugin
