# aios/plugins/manager.py - 插件管理器
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .base import AIOSPlugin, PluginMeta, PluginStatus, PluginType
from .registry import get_registry, get_capability_registry
from .eventbus import get_bus, EventBus

logger = logging.getLogger(__name__)


class PluginManager:
    """AIOS 插件管理器"""

    def __init__(self, plugin_dir: Optional[Path] = None, bus: Optional[EventBus] = None):
        """
        初始化插件管理器

        Args:
            plugin_dir: 插件目录，默认为 aios/plugins
            bus: 事件总线，默认使用全局实例
        """
        if plugin_dir is None:
            plugin_dir = Path(__file__).parent
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, AIOSPlugin] = {}
        self._plugin_modules: Dict[str, Any] = {}
        self.registry = get_registry()
        self.capability_registry = get_capability_registry()
        self.bus = bus or get_bus()
        self.plugin_stats: Dict[str, Dict[str, Any]] = {}  # 插件统计

        # 自动加载已启用的插件
        self._auto_load()

    def discover(self) -> List[str]:
        """
        发现可用插件

        Returns:
            插件名称列表
        """
        plugins = []
        if not self.plugin_dir.exists():
            logger.warning(f"插件目录不存在: {self.plugin_dir}")
            return plugins

        # 扫描当前目录
        for item in self.plugin_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                # 检查是否有 plugin.py 或 __init__.py
                if (item / "plugin.py").exists() or (item / "__init__.py").exists():
                    plugins.append(item.name)

        # 扫描 builtin 目录
        builtin_dir = self.plugin_dir / "builtin"
        if builtin_dir.exists():
            for item in builtin_dir.iterdir():
                if item.is_dir() and not item.name.startswith("_"):
                    if (item / "plugin.py").exists():
                        plugins.append(f"builtin/{item.name}")

        return plugins

    def load(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        加载插件

        Args:
            name: 插件名称（支持 "builtin/xxx" 格式）
            config: 插件配置

        Returns:
            是否加载成功
        """
        if name in self.plugins:
            logger.warning(f"插件 {name} 已加载")
            return True

        # 处理 builtin/ 前缀
        plugin_path = self.plugin_dir / name
        if not plugin_path.exists():
            logger.error(f"插件目录不存在: {plugin_path}")
            return False

        try:
            # 尝试加载 plugin.py
            plugin_file = plugin_path / "plugin.py"
            if plugin_file.exists():
                # 使用 name 替换 / 为 .
                module_name = f"aios.plugins.{name.replace('/', '.')}.plugin"
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            else:
                # 尝试加载 __init__.py
                module = importlib.import_module(f"aios.plugins.{name}")

            # 查找插件类
            # 优先使用 PLUGIN_CLASS
            if hasattr(module, 'PLUGIN_CLASS'):
                plugin_class = module.PLUGIN_CLASS
            else:
                # 查找继承自 AIOSPlugin 的类（排除基类）
                plugin_class = None
                from plugins.base import (
                    AIOSPlugin, SensorPlugin, ReactorPlugin, 
                    NotifierPlugin, DashboardPlugin, IntegrationPlugin
                )
                base_classes = {AIOSPlugin, SensorPlugin, ReactorPlugin, 
                               NotifierPlugin, DashboardPlugin, IntegrationPlugin}
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, AIOSPlugin)
                        and attr not in base_classes
                    ):
                        plugin_class = attr
                        break

            if plugin_class is None:
                logger.error(f"插件 {name} 中未找到插件类")
                return False

            # 实例化插件
            plugin = plugin_class()
            plugin.status = PluginStatus.LOADING

            # 加载配置
            if config is None:
                config = self._load_config(name)

            # 初始化插件
            if not plugin.init(config):
                logger.error(f"插件 {name} 初始化失败")
                plugin.status = PluginStatus.ERROR
                return False

            plugin.config = config
            plugin.status = PluginStatus.LOADED

            # 调用 register 钩子（注册能力）
            plugin.register(self.capability_registry)

            # 调用 on_load 钩子
            plugin.on_load()

            # 自动订阅事件
            for pattern in plugin.subscriptions():
                self.bus.subscribe(pattern, self._safe_handler(name, plugin), plugin_name=name)

            self.plugins[name] = plugin
            self._plugin_modules[name] = module

            # 注册到注册表
            self.registry.register(name, enabled=True, config=config)

            logger.info(f"插件 {name} 加载成功")
            return True

        except Exception as e:
            logger.error(f"加载插件 {name} 失败: {e}", exc_info=True)
            return False

    def unload(self, name: str) -> bool:
        """
        卸载插件

        Args:
            name: 插件名称

        Returns:
            是否卸载成功
        """
        if name not in self.plugins:
            logger.warning(f"插件 {name} 未加载")
            return False

        try:
            plugin = self.plugins[name]

            # 取消事件订阅
            self.bus.unsubscribe_plugin(name)

            # 调用 on_unload 钩子
            plugin.on_unload()

            plugin.status = PluginStatus.UNLOADED

            # 移除插件
            del self.plugins[name]
            if name in self._plugin_modules:
                del self._plugin_modules[name]

            # 从注册表注销
            self.registry.unregister(name)

            logger.info(f"插件 {name} 卸载成功")
            return True

        except Exception as e:
            logger.error(f"卸载插件 {name} 失败: {e}", exc_info=True)
            return False

    def reload(self, name: str) -> bool:
        """
        重载插件

        Args:
            name: 插件名称

        Returns:
            是否重载成功
        """
        if name not in self.plugins:
            logger.warning(f"插件 {name} 未加载，尝试加载")
            return self.load(name)

        # 保存配置
        config = self.plugins[name].config

        # 卸载
        if not self.unload(name):
            return False

        # 重新加载
        return self.load(name, config)

    def list(self) -> List[PluginMeta]:
        """
        列出已加载插件

        Returns:
            插件元信息列表
        """
        return [plugin.meta() for plugin in self.plugins.values()]

    def get(self, name: str) -> Optional[AIOSPlugin]:
        """
        获取插件实例

        Args:
            name: 插件名称

        Returns:
            插件实例，如果不存在返回 None
        """
        return self.plugins.get(name)

    def call(self, name: str, method: str, *args, **kwargs) -> Any:
        """
        调用插件方法

        Args:
            name: 插件名称
            method: 方法名
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            方法返回值

        Raises:
            ValueError: 插件不存在或方法不存在
        """
        plugin = self.get(name)
        if plugin is None:
            raise ValueError(f"插件 {name} 不存在")

        if not hasattr(plugin, method):
            raise ValueError(f"插件 {name} 没有方法 {method}")

        return getattr(plugin, method)(*args, **kwargs)

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        检查所有插件健康状态

        Returns:
            插件健康状态字典 {name: health_status}
        """
        results = {}
        for name, plugin in self.plugins.items():
            try:
                results[name] = plugin.health_check()
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        return results

    def _load_config(self, name: str) -> Dict[str, Any]:
        """
        加载插件配置

        Args:
            name: 插件名称

        Returns:
            配置字典
        """
        config_file = self.plugin_dir / name / "config.yaml"
        if not config_file.exists():
            return {}

        try:
            import yaml

            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载插件 {name} 配置失败: {e}")
            return {}

    def enable(self, name: str) -> bool:
        """
        启用插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self.get(name)
        if plugin is None:
            return self.load(name)

        if plugin.status == PluginStatus.DISABLED:
            plugin.status = PluginStatus.LOADED
            self.registry.enable(name)
            logger.info(f"插件 {name} 已启用")
            return True

        return True

    def disable(self, name: str) -> bool:
        """
        禁用插件

        Args:
            name: 插件名称

        Returns:
            是否成功
        """
        plugin = self.get(name)
        if plugin is None:
            logger.warning(f"插件 {name} 不存在")
            return False

        plugin.status = PluginStatus.DISABLED
        self.registry.disable(name)
        logger.info(f"插件 {name} 已禁用")
        return True


    def _auto_load(self) -> None:
        """自动加载已启用的插件"""
        for name in self.registry.list_enabled():
            try:
                config = self.registry.get_config(name)
                self.load(name, config)
            except Exception as e:
                logger.error(f"自动加载插件 {name} 失败: {e}")

    def _safe_handler(self, name: str, plugin: AIOSPlugin):
        """
        创建安全的事件处理器（带统计和错误捕获）

        Args:
            name: 插件名称
            plugin: 插件实例

        Returns:
            安全的处理函数
        """
        import time

        def handler(event: Dict[str, Any]):
            t0 = time.perf_counter()
            ok = True
            err = None
            try:
                plugin.on_event(event)
            except Exception as e:
                ok = False
                err = repr(e)
                logger.error(f"插件 {name} 处理事件失败: {e}", exc_info=True)
            finally:
                dt_ms = (time.perf_counter() - t0) * 1000.0
                st = self.plugin_stats.setdefault(
                    name,
                    {
                        "calls": 0,
                        "ok": 0,
                        "fail": 0,
                        "avg_ms": 0.0,
                        "last_err": None,
                    },
                )
                st["calls"] += 1
                if ok:
                    st["ok"] += 1
                else:
                    st["fail"] += 1
                    st["last_err"] = err
                # EMA 平滑
                alpha = 0.2
                st["avg_ms"] = st["avg_ms"] * (1 - alpha) + dt_ms * alpha

        return handler


# 全局插件管理器实例
_manager: Optional[PluginManager] = None


def get_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager
