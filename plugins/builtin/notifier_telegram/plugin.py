# aios/plugins/builtin/notifier_telegram/plugin.py
from typing import Dict, Any
import sys
from pathlib import Path
import requests
import time

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import NotifierPlugin, PluginMeta, PluginType


class TelegramNotifierPlugin(NotifierPlugin):
    """Telegram 通知插件"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="notifier_telegram",
            version="1.0.0",
            description="Telegram 通知插件（发送告警到 Telegram）",
            author="小九",
            plugin_type=PluginType.NOTIFIER,
            capabilities=["send", "rich_text"],
        )

    def subscriptions(self) -> list:
        """订阅错误和告警事件"""
        return ["event.*error*", "event.*failed*", "alert.*"]

    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        self._bot_token = config.get("bot_token")
        self._chat_id = config.get("chat_id")
        self._min_severity = config.get("min_severity", "warn")  # info/warn/error/critical
        self._rate_limit = config.get("rate_limit", 5)  # 最多每5秒发送一次
        self._last_send_time = 0

        if not self._bot_token or not self._chat_id:
            print("❌ Telegram Notifier 初始化失败: 缺少 bot_token 或 chat_id")
            return False

        print(f"✅ Telegram Notifier 初始化成功")
        print(f"   Chat ID: {self._chat_id}")
        print(f"   最小级别: {self._min_severity}")
        return True

    def send(self, message: str, level: str = "info") -> bool:
        """
        发送通知到 Telegram

        Args:
            message: 通知内容
            level: 通知级别（info/warn/error/critical）

        Returns:
            是否发送成功
        """
        # 检查级别
        severity_order = {"info": 0, "warn": 1, "error": 2, "critical": 3}
        if severity_order.get(level, 0) < severity_order.get(self._min_severity, 0):
            return True  # 级别不够，跳过

        # 速率限制
        now = time.time()
        if now - self._last_send_time < self._rate_limit:
            return True  # 速率限制，跳过

        try:
            # 级别图标
            icons = {
                "info": "ℹ️",
                "warn": "⚠️",
                "error": "❌",
                "critical": "🚨",
            }
            icon = icons.get(level, "📢")

            # 格式化消息
            formatted_message = f"{icon} *[{level.upper()}]* {message}"

            # 发送到 Telegram
            url = f"https://api.telegram.org/bot{self._bot_token}/sendMessage"
            data = {
                "chat_id": self._chat_id,
                "text": formatted_message,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()

            self._last_send_time = now
            return True

        except Exception as e:
            print(f"❌ Telegram Notifier 发送失败: {e}")
            return False

    def supports_rich_text(self) -> bool:
        """是否支持富文本"""
        return True

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self._bot_token or not self._chat_id:
            return {
                "status": "error",
                "message": "缺少配置",
            }

        try:
            # 测试 API 连接
            url = f"https://api.telegram.org/bot{self._bot_token}/getMe"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            return {
                "status": "ok",
                "message": "Telegram 连接正常",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"连接失败: {e}",
            }

    def on_event(self, event: Dict[str, Any]) -> None:
        """监听事件，自动发送告警"""
        severity = event.get("severity", "info")
        topic = event.get("topic", "unknown")
        data = event.get("data", {})

        # 构建消息
        message_parts = [f"*事件:* `{topic}`"]

        # 添加错误信息
        if "error" in data:
            message_parts.append(f"*错误:* {data['error']}")

        # 添加告警信息
        alerts = data.get("alerts", [])
        if alerts:
            message_parts.append("*告警:*")
            for alert in alerts[:3]:  # 最多显示3个
                message_parts.append(f"  • {alert}")

        # 添加其他关键信息
        for key in ["provider", "task", "category"]:
            if key in data:
                message_parts.append(f"*{key.title()}:* {data[key]}")

        message = "\n".join(message_parts)
        self.send(message, severity)


# 导出插件类
PLUGIN_CLASS = TelegramNotifierPlugin
