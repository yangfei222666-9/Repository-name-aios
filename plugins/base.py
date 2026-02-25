# aios/plugins/base.py - 插件基类
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class PluginType(Enum):
    """插件类型"""

    SENSOR = "sensor"
    REACTOR = "reactor"
    NOTIFIER = "notifier"
    DASHBOARD = "dashboard"
    INTEGRATION = "integration"


class PluginStatus(Enum):
    """插件状态"""

    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    RUNNING = "running"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class PluginMeta:
    """插件元信息"""

    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    repository: Optional[str] = None
    license: str = "MIT"


class AIOSPlugin(ABC):
    """AIOS 插件基类"""

    def __init__(self):
        self._status = PluginStatus.UNLOADED
        self._config: Dict[str, Any] = {}

    @abstractmethod
    def meta(self) -> PluginMeta:
        """插件元信息"""
        pass

    @abstractmethod
    def init(self, config: Dict[str, Any]) -> bool:
        """
        初始化插件

        Args:
            config: 插件配置

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态字典，至少包含 'status' 字段（ok/warn/error）
        """
        pass

    def on_load(self) -> None:
        """插件加载时调用（可选）"""
        pass

    def on_unload(self) -> None:
        """插件卸载时调用（可选）"""
        pass

    def on_event(self, event: Dict[str, Any]) -> None:
        """事件触发时调用（可选）"""
        pass

    def register(self, registry: Any) -> None:
        """
        注册插件能力（可选）

        Args:
            registry: CapabilityRegistry 实例
        """
        pass

    def subscriptions(self) -> List[str]:
        """
        声明订阅的 topic pattern（可选）

        Returns:
            topic 模式列表，默认订阅 event.*
        """
        return ["event.*"]

    @property
    def status(self) -> PluginStatus:
        """获取插件状态"""
        return self._status

    @status.setter
    def status(self, value: PluginStatus):
        """设置插件状态"""
        self._status = value

    @property
    def config(self) -> Dict[str, Any]:
        """获取插件配置"""
        return self._config

    @config.setter
    def config(self, value: Dict[str, Any]):
        """设置插件配置"""
        self._config = value


class SensorPlugin(AIOSPlugin):
    """Sensor 插件基类（数据采集）"""

    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """
        采集数据

        Returns:
            事件列表
        """
        pass

    def interval(self) -> int:
        """
        采集间隔（秒）

        Returns:
            间隔秒数，默认 60 秒
        """
        return 60


class ReactorPlugin(AIOSPlugin):
    """Reactor 插件基类（自动修复）"""

    @abstractmethod
    def match(self, event: Dict[str, Any]) -> bool:
        """
        判断是否匹配此事件

        Args:
            event: 事件字典

        Returns:
            是否匹配
        """
        pass

    @abstractmethod
    def react(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成修复动作

        Args:
            event: 事件字典

        Returns:
            动作字典
        """
        pass

    def verify(self, action: Dict[str, Any]) -> bool:
        """
        验证修复是否成功（可选）

        Args:
            action: 动作字典

        Returns:
            是否成功
        """
        return True


class NotifierPlugin(AIOSPlugin):
    """Notifier 插件基类（通知渠道）"""

    @abstractmethod
    def send(self, message: str, level: str = "info") -> bool:
        """
        发送通知

        Args:
            message: 通知内容
            level: 通知级别（info/warn/error/critical）

        Returns:
            是否发送成功
        """
        pass

    def supports_rich_text(self) -> bool:
        """
        是否支持富文本（Markdown/HTML）

        Returns:
            是否支持
        """
        return False


class DashboardPlugin(AIOSPlugin):
    """Dashboard 插件基类（监控面板）"""

    @abstractmethod
    def render(self) -> str:
        """
        渲染面板

        Returns:
            HTML/JSON 字符串
        """
        pass

    def api_routes(self) -> Dict[str, Any]:
        """
        自定义 API 路由

        Returns:
            路由字典 {path: handler}
        """
        return {}


class IntegrationPlugin(AIOSPlugin):
    """Integration 插件基类（第三方集成）"""

    def webhook(self, data: Dict[str, Any]) -> None:
        """
        接收外部 webhook

        Args:
            data: webhook 数据
        """
        pass
