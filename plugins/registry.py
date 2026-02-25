# aios/plugins/registry.py - 插件注册表（持久化 + 能力注册）
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class CapabilityRegistry:
    """能力注册表 - 插件注册技能/任务/路由/指标"""

    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}  # name -> {fn, schema}
        self.tasks: Dict[str, Dict[str, Any]] = {}  # name -> task_def
        self.routes: Dict[str, Callable] = {}  # path -> handler
        self.metrics: Dict[str, Dict[str, Any]] = {}  # name -> schema

    def register_skill(
        self, name: str, fn: Callable, schema: Optional[Dict] = None
    ) -> None:
        """
        注册技能

        Args:
            name: 技能名称
            fn: 技能函数
            schema: 技能参数 schema（可选）
        """
        self.skills[name] = {"fn": fn, "schema": schema or {}}
        logger.info(f"注册技能: {name}")

    def register_task(self, name: str, task_def: Dict[str, Any]) -> None:
        """
        注册任务

        Args:
            name: 任务名称
            task_def: 任务定义
        """
        self.tasks[name] = task_def
        logger.info(f"注册任务: {name}")

    def register_route(self, path: str, handler: Callable) -> None:
        """
        注册路由（Web UI）

        Args:
            path: 路由路径
            handler: 处理函数
        """
        self.routes[path] = handler
        logger.info(f"注册路由: {path}")

    def register_metric(self, name: str, schema: Dict[str, Any]) -> None:
        """
        注册指标

        Args:
            name: 指标名称
            schema: 指标 schema
        """
        self.metrics[name] = schema
        logger.info(f"注册指标: {name}")

    def get_skill(self, name: str) -> Optional[Callable]:
        """获取技能函数"""
        skill = self.skills.get(name)
        return skill["fn"] if skill else None

    def get_task(self, name: str) -> Optional[Dict[str, Any]]:
        """获取任务定义"""
        return self.tasks.get(name)

    def get_route(self, path: str) -> Optional[Callable]:
        """获取路由处理函数"""
        return self.routes.get(path)

    def list_skills(self) -> List[str]:
        """列出所有技能"""
        return list(self.skills.keys())

    def list_tasks(self) -> List[str]:
        """列出所有任务"""
        return list(self.tasks.keys())

    def list_routes(self) -> List[str]:
        """列出所有路由"""
        return list(self.routes.keys())


class PluginRegistry:
    """插件注册表（持久化到文件）"""

    def __init__(self, registry_file: Optional[Path] = None):
        """
        初始化注册表

        Args:
            registry_file: 注册表文件路径，默认为 aios/runtime/plugins_state.json
        """
        if registry_file is None:
            registry_file = Path(__file__).parent.parent / "runtime" / "plugins_state.json"

        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

        self._data: Dict[str, Dict] = self._load()

    def _load(self) -> Dict[str, Dict]:
        """加载注册表"""
        if not self.registry_file.exists():
            return {}

        try:
            with open(self.registry_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载插件注册表失败: {e}")
            return {}

    def _save(self) -> None:
        """保存注册表"""
        try:
            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存插件注册表失败: {e}")

    def register(
        self, name: str, enabled: bool = True, config: Optional[Dict] = None
    ) -> None:
        """
        注册插件

        Args:
            name: 插件名称
            enabled: 是否启用
            config: 插件配置
        """
        self._data[name] = {
            "enabled": enabled,
            "config": config or {},
        }
        self._save()

    def unregister(self, name: str) -> None:
        """
        注销插件

        Args:
            name: 插件名称
        """
        if name in self._data:
            del self._data[name]
            self._save()

    def is_enabled(self, name: str) -> bool:
        """
        检查插件是否启用

        Args:
            name: 插件名称

        Returns:
            是否启用
        """
        return self._data.get(name, {}).get("enabled", False)

    def get_config(self, name: str) -> Dict:
        """
        获取插件配置

        Args:
            name: 插件名称

        Returns:
            配置字典
        """
        return self._data.get(name, {}).get("config", {})

    def list_enabled(self) -> List[str]:
        """
        列出所有启用的插件

        Returns:
            插件名称列表
        """
        return [name for name, data in self._data.items() if data.get("enabled", False)]

    def list_all(self) -> List[str]:
        """
        列出所有注册的插件

        Returns:
            插件名称列表
        """
        return list(self._data.keys())

    def enable(self, name: str) -> None:
        """
        启用插件

        Args:
            name: 插件名称
        """
        if name in self._data:
            self._data[name]["enabled"] = True
            self._save()

    def disable(self, name: str) -> None:
        """
        禁用插件

        Args:
            name: 插件名称
        """
        if name in self._data:
            self._data[name]["enabled"] = False
            self._save()


# 全局注册表实例
_registry: Optional[PluginRegistry] = None
_capability_registry: Optional[CapabilityRegistry] = None


def get_registry() -> PluginRegistry:
    """获取全局注册表实例"""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def get_capability_registry() -> CapabilityRegistry:
    """获取全局能力注册表实例"""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()
    return _capability_registry
