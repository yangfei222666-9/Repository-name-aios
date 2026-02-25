# aios/plugins/builtin/sensor_disk_space/plugin.py
from typing import Dict, Any, List
import time
import sys
from pathlib import Path
import psutil

AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import SensorPlugin, PluginMeta, PluginType


class DiskSpaceSensorPlugin(SensorPlugin):
    """磁盘空间监控插件"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="sensor_disk_space",
            version="1.0.0",
            description="磁盘空间监控（>90% 告警）",
            author="小九",
            plugin_type=PluginType.SENSOR,
            capabilities=["collect", "threshold_alert"],
        )

    def subscriptions(self) -> list:
        return []

    def init(self, config: Dict[str, Any]) -> bool:
        self._thresholds = config.get("thresholds", {
            "warn": 80,
            "critical": 90,
        })
        self._monitored_drives = config.get("monitored_drives", ["C:", "D:", "E:"])
        print(f"✅ Disk Space Sensor 初始化成功，监控: {self._monitored_drives}")
        return True

    def collect(self) -> List[Dict[str, Any]]:
        events = []
        timestamp = int(time.time())

        for drive in self._monitored_drives:
            try:
                usage = psutil.disk_usage(drive)
                percent = usage.percent
                free_gb = usage.free / (1024**3)
                total_gb = usage.total / (1024**3)
                
                alerts = []
                severity = "info"
                
                if percent >= self._thresholds["critical"]:
                    alerts.append(f"🚨 {drive} 磁盘空间严重不足: {percent}% (剩余 {free_gb:.1f}GB)")
                    severity = "critical"
                elif percent >= self._thresholds["warn"]:
                    alerts.append(f"⚠️ {drive} 磁盘空间不足: {percent}% (剩余 {free_gb:.1f}GB)")
                    severity = "warn"
                
                event = {
                    "timestamp": timestamp,
                    "topic": "event.disk.space",
                    "category": "disk_space",
                    "data": {
                        "drive": drive,
                        "percent": round(percent, 1),
                        "free_gb": round(free_gb, 1),
                        "total_gb": round(total_gb, 1),
                        "alerts": alerts,
                    },
                    "severity": severity,
                }
                
                events.append(event)
            
            except Exception as e:
                events.append({
                    "timestamp": timestamp,
                    "topic": "event.disk.error",
                    "category": "disk_error",
                    "data": {"drive": drive, "error": str(e)},
                    "severity": "error",
                })
        
        return events

    def interval(self) -> int:
        return self.config.get("interval", 600)  # 10分钟

    def health_check(self) -> Dict[str, Any]:
        try:
            events = self.collect()
            has_error = any(e.get("category") == "disk_error" for e in events)
            
            if has_error:
                return {"status": "error", "message": "磁盘数据采集失败"}
            
            return {"status": "ok", "message": f"监控 {len(self._monitored_drives)} 个磁盘"}
        except Exception as e:
            return {"status": "error", "message": f"健康检查失败: {e}"}


PLUGIN_CLASS = DiskSpaceSensorPlugin
