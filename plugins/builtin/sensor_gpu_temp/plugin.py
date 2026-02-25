# aios/plugins/builtin/sensor_gpu_temp/plugin.py
from typing import Dict, Any, List
import time
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).parent.parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

from plugins.base import SensorPlugin, PluginMeta, PluginType


class GPUTempSensorPlugin(SensorPlugin):
    """GPU 温度监控插件（RTX 5070 Ti）"""

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="sensor_gpu_temp",
            version="1.0.0",
            description="GPU 温度监控（RTX 5070 Ti 专用）",
            author="小九",
            plugin_type=PluginType.SENSOR,
            capabilities=["collect", "threshold_alert"],
        )

    def subscriptions(self) -> list:
        return []  # Sensor 不订阅

    def init(self, config: Dict[str, Any]) -> bool:
        if not PYNVML_AVAILABLE:
            print("❌ pynvml 未安装")
            return False

        try:
            pynvml.nvmlInit()
            self._device_count = pynvml.nvmlDeviceGetCount()
            self._thresholds = config.get("thresholds", {
                "temperature_warn": 75,
                "temperature_critical": 85,
                "memory_warn": 85,
                "power_warn": 250,
            })
            print(f"✅ GPU Temp Sensor 初始化成功，检测到 {self._device_count} 个 GPU")
            return True
        except Exception as e:
            print(f"❌ GPU Temp Sensor 初始化失败: {e}")
            return False

    def collect(self) -> List[Dict[str, Any]]:
        if not PYNVML_AVAILABLE:
            return []

        events = []
        timestamp = int(time.time())

        try:
            for i in range(self._device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU 名称
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")
                
                # 温度
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # 显存
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_percent = (mem_info.used / mem_info.total) * 100
                
                # 功率
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # W
                except:
                    power = 0
                
                # 检查阈值
                alerts = []
                severity = "info"
                
                if temp >= self._thresholds["temperature_critical"]:
                    alerts.append(f"🔥 温度危险: {temp}°C")
                    severity = "critical"
                elif temp >= self._thresholds["temperature_warn"]:
                    alerts.append(f"⚠️ 温度过高: {temp}°C")
                    severity = "warn"
                
                if memory_percent >= self._thresholds["memory_warn"]:
                    alerts.append(f"💾 显存使用率过高: {memory_percent:.1f}%")
                    if severity == "info":
                        severity = "warn"
                
                if power >= self._thresholds["power_warn"]:
                    alerts.append(f"⚡ 功率过高: {power:.1f}W")
                    if severity == "info":
                        severity = "warn"
                
                event = {
                    "timestamp": timestamp,
                    "topic": "event.gpu.temperature",
                    "category": "gpu_temp",
                    "data": {
                        "gpu_id": i,
                        "name": name,
                        "temperature": temp,
                        "memory_percent": round(memory_percent, 1),
                        "power_w": round(power, 1),
                        "alerts": alerts,
                    },
                    "severity": severity,
                }
                
                events.append(event)
        
        except Exception as e:
            events.append({
                "timestamp": timestamp,
                "topic": "event.gpu.error",
                "category": "gpu_error",
                "data": {"error": str(e)},
                "severity": "error",
            })
        
        return events

    def interval(self) -> int:
        return self.config.get("interval", 300)  # 5分钟

    def health_check(self) -> Dict[str, Any]:
        if not PYNVML_AVAILABLE:
            return {"status": "error", "message": "pynvml 未安装"}
        
        try:
            events = self.collect()
            has_error = any(e.get("category") == "gpu_error" for e in events)
            
            if has_error:
                return {"status": "error", "message": "GPU 数据采集失败"}
            
            return {"status": "ok", "message": f"{self._device_count} 个 GPU 正常"}
        except Exception as e:
            return {"status": "error", "message": f"健康检查失败: {e}"}

    def on_unload(self) -> None:
        if PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass


PLUGIN_CLASS = GPUTempSensorPlugin
