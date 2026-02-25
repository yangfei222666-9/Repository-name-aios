# aios/plugins/builtin/notifier_console/plugin.py
from typing import Dict, Any
import sys
from pathlib import Path
from datetime import datetime

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import NotifierPlugin, PluginMeta, PluginType


class ConsoleNotifierPlugin(NotifierPlugin):
    """控制台通知插件（打印告警）"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="notifier_console",
            version="1.0.0",
            description="控制台通知插件（打印告警到终端）",
            author="小九",
            plugin_type=PluginType.NOTIFIER,
            capabilities=["send", "rich_text"],
        )

    def subscriptions(self) -> list:
        """订阅错误和告警事件"""
        return ["event.*error*", "event.*failed*", "alert.*"]

    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        self._show_timestamp = config.get("show_timestamp", True)
        self._color_enabled = config.get("color_enabled", True)
        print(f"Console Notifier 初始化成功")
        return True

    def send(self, message: str, level: str = "info") -> bool:
        """
        发送通知到控制台

        Args:
            message: 通知内容
            level: 通知级别（info/warn/error/critical）

        Returns:
            是否发送成功
        """
        try:
            # 级别图标
            icons = {
                "info": "ℹ️",
                "warn": "⚠️",
                "error": "❌",
                "critical": "🚨",
            }
            icon = icons.get(level, "📢")

            # 时间戳
            timestamp = ""
            if self._show_timestamp:
                timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] "

            # 颜色（ANSI）
            colors = {
                "info": "\033[36m",  # 青色
                "warn": "\033[33m",  # 黄色
                "error": "\033[31m",  # 红色
                "critical": "\033[35m",  # 紫色
            }
            reset = "\033[0m"

            if self._color_enabled:
                color = colors.get(level, "")
                print(f"{timestamp}{icon} {color}[{level.upper()}]{reset} {message}")
            else:
                print(f"{timestamp}{icon} [{level.upper()}] {message}")

            return True

        except Exception as e:
            print(f"❌ Console Notifier 发送失败: {e}")
            return False

    def supports_rich_text(self) -> bool:
        """是否支持富文本"""
        return False

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 测试发送
            self.send("健康检查测试", "info")
            return {
                "status": "ok",
                "message": "控制台通知正常",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {e}",
            }

    def on_event(self, event: Dict[str, Any]) -> None:
        """监听事件，自动发送告警"""
        severity = event.get("severity", "info")
        category = event.get("category", "unknown")

        # 只处理 warn/error/critical
        if severity in ("warn", "error", "critical"):
            data = event.get("data", {})
            alerts = data.get("alerts", [])

            if alerts:
                for alert in alerts:
                    self.send(f"[{category}] {alert}", severity)


# 导出插件类
PLUGIN_CLASS = ConsoleNotifierPlugin
