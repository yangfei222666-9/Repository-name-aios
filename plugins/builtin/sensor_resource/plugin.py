# aios/plugins/builtin/sensor_resource/plugin.py
import time
import psutil
from typing import Dict, Any, List
import sys
from pathlib import Path

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import SensorPlugin, PluginMeta, PluginType


class ResourceSensorPlugin(SensorPlugin):
    """系统资源监控插件（CPU、内存、磁盘）"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="sensor_resource",
            version="1.0.0",
            description="系统资源监控（CPU、内存、磁盘）",
            author="小九",
            plugin_type=PluginType.SENSOR,
            capabilities=["collect", "threshold_alert"],
        )

    def subscriptions(self) -> list:
        """Sensor 不订阅事件，自己产出事件"""
        return []

    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        self._thresholds = config.get(
            "thresholds",
            {
                "cpu_percent": 80,
                "memory_percent": 85,
                "disk_percent": 90,
            },
        )
        print(f"Resource Sensor 初始化成功")
        return True

    def collect(self) -> List[Dict[str, Any]]:
        """采集系统资源数据"""
        timestamp = int(time.time())
        events = []

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()

            # 内存
            mem = psutil.virtual_memory()
            memory_percent = mem.percent
            memory_used_gb = mem.used / (1024**3)
            memory_total_gb = mem.total / (1024**3)

            # 磁盘
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # 构建事件
            event = {
                "timestamp": timestamp,
                "layer": "KERNEL",
                "category": "resource",
                "data": {
                    "cpu_percent": round(cpu_percent, 2),
                    "cpu_count": cpu_count,
                    "memory_percent": round(memory_percent, 2),
                    "memory_used_gb": round(memory_used_gb, 2),
                    "memory_total_gb": round(memory_total_gb, 2),
                    "disk_percent": round(disk_percent, 2),
                    "disk_used_gb": round(disk_used_gb, 2),
                    "disk_total_gb": round(disk_total_gb, 2),
                },
            }

            # 检查阈值
            alerts = []
            if cpu_percent >= self._thresholds["cpu_percent"]:
                alerts.append(f"CPU 使用率过高: {cpu_percent}%")
            if memory_percent >= self._thresholds["memory_percent"]:
                alerts.append(f"内存使用率过高: {memory_percent}%")
            if disk_percent >= self._thresholds["disk_percent"]:
                alerts.append(f"磁盘使用率过高: {disk_percent}%")

            if alerts:
                event["data"]["alerts"] = alerts
                event["severity"] = "warn"

            events.append(event)

        except Exception as e:
            events.append(
                {
                    "timestamp": timestamp,
                    "layer": "KERNEL",
                    "category": "resource_error",
                    "data": {"error": str(e)},
                    "severity": "error",
                }
            )

        return events

    def interval(self) -> int:
        """采集间隔（秒）"""
        return self.config.get("interval", 60)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 尝试采集一次数据
            events = self.collect()
            has_error = any(e.get("category") == "resource_error" for e in events)

            if has_error:
                return {
                    "status": "error",
                    "message": "资源数据采集失败",
                }

            return {
                "status": "ok",
                "message": "资源监控正常",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {e}",
            }


# 导出插件类
PLUGIN_CLASS = ResourceSensorPlugin
