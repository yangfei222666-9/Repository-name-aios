# aios/plugins/gpu_sensor/plugin.py - GPU 监控插件
from typing import Dict, Any, List
import time
import sys
from pathlib import Path

# 添加 aios 到 sys.path
AIOS_ROOT = Path(__file__).parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

try:
    import pynvml

    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False

from plugins.base import SensorPlugin, PluginMeta, PluginType


class GPUSensorPlugin(SensorPlugin):
    """GPU 监控插件（基于 NVIDIA pynvml）"""

    def __init__(self):
        super().__init__()
        self._initialized = False
        self._device_count = 0
        self._thresholds = {
            "temperature": 85,
            "memory_usage": 90,
            "utilization": 95,
        }

    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="gpu_sensor",
            version="1.0.0",
            description="GPU 监控插件（温度、显存、使用率）",
            author="小九",
            plugin_type=PluginType.SENSOR,
            capabilities=["collect", "threshold_alert"],
            dependencies=["pynvml"],
            repository="https://github.com/aios-plugins/gpu-sensor",
        )

    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        if not PYNVML_AVAILABLE:
            print("警告: pynvml 未安装，GPU 监控功能不可用")
            return False

        try:
            pynvml.nvmlInit()
            self._device_count = pynvml.nvmlDeviceGetCount()
            self._initialized = True

            # 加载配置
            if "thresholds" in config:
                self._thresholds.update(config["thresholds"])

            print(f"GPU Sensor 初始化成功，检测到 {self._device_count} 个 GPU")
            return True

        except Exception as e:
            print(f"GPU Sensor 初始化失败: {e}")
            return False

    def collect(self) -> List[Dict[str, Any]]:
        """采集 GPU 数据"""
        if not self._initialized:
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
                temperature = pynvml.nvmlDeviceGetTemperature(
                    handle, pynvml.NVML_TEMPERATURE_GPU
                )

                # 显存
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_used = mem_info.used / 1024**3  # GB
                memory_total = mem_info.total / 1024**3  # GB
                memory_usage = (mem_info.used / mem_info.total) * 100

                # 使用率
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = utilization.gpu
                mem_util = utilization.memory

                # 功率
                try:
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000  # W
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000
                except:
                    power_usage = 0
                    power_limit = 0

                # 构建事件
                event = {
                    "timestamp": timestamp,
                    "layer": "KERNEL",
                    "category": "gpu",
                    "data": {
                        "gpu_id": i,
                        "name": name,
                        "temperature": temperature,
                        "memory_used_gb": round(memory_used, 2),
                        "memory_total_gb": round(memory_total, 2),
                        "memory_usage_percent": round(memory_usage, 2),
                        "gpu_utilization": gpu_util,
                        "memory_utilization": mem_util,
                        "power_usage_w": round(power_usage, 2),
                        "power_limit_w": round(power_limit, 2),
                    },
                }

                # 检查阈值
                alerts = []
                if temperature >= self._thresholds["temperature"]:
                    alerts.append(f"温度过高: {temperature}°C")
                if memory_usage >= self._thresholds["memory_usage"]:
                    alerts.append(f"显存使用率过高: {memory_usage:.1f}%")
                if gpu_util >= self._thresholds["utilization"]:
                    alerts.append(f"GPU 使用率过高: {gpu_util}%")

                if alerts:
                    event["data"]["alerts"] = alerts
                    event["severity"] = "warn"

                events.append(event)

        except Exception as e:
            events.append(
                {
                    "timestamp": timestamp,
                    "layer": "KERNEL",
                    "category": "gpu_error",
                    "data": {"error": str(e)},
                    "severity": "error",
                }
            )

        return events

    def interval(self) -> int:
        """采集间隔（秒）"""
        return self.config.get("interval", 30)

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not PYNVML_AVAILABLE:
            return {
                "status": "error",
                "message": "pynvml 未安装",
            }

        if not self._initialized:
            return {
                "status": "error",
                "message": "未初始化",
            }

        try:
            # 尝试采集一次数据
            events = self.collect()
            has_error = any(e.get("category") == "gpu_error" for e in events)

            if has_error:
                return {
                    "status": "error",
                    "message": "GPU 数据采集失败",
                }

            return {
                "status": "ok",
                "message": f"{self._device_count} 个 GPU 正常",
                "gpu_count": self._device_count,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {e}",
            }

    def on_unload(self) -> None:
        """卸载时清理"""
        if self._initialized and PYNVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
