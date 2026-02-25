# GPU Sensor Plugin

GPU 监控插件，基于 NVIDIA pynvml 库。

## 功能

- 实时监控 GPU 温度、显存、使用率
- 阈值告警
- 多 GPU 支持
- 功率监控

## 依赖

```bash
pip install pynvml
```

## 配置

编辑 `config.yaml`：

```yaml
enabled: true
interval: 30  # 采集间隔（秒）

thresholds:
  temperature: 85  # 温度阈值（℃）
  memory_usage: 90  # 显存使用率阈值（%）
  utilization: 95  # GPU 使用率阈值（%）

notify_on_threshold: true
```

## 使用

```bash
# 加载插件
aios plugin load gpu_sensor

# 查看状态
aios plugin health gpu_sensor

# 卸载插件
aios plugin unload gpu_sensor
```

## 数据格式

```json
{
  "timestamp": 1708761600,
  "layer": "KERNEL",
  "category": "gpu",
  "data": {
    "gpu_id": 0,
    "name": "NVIDIA GeForce RTX 5070 Ti",
    "temperature": 65,
    "memory_used_gb": 8.5,
    "memory_total_gb": 16.0,
    "memory_usage_percent": 53.1,
    "gpu_utilization": 75,
    "memory_utilization": 60,
    "power_usage_w": 220.5,
    "power_limit_w": 285.0
  }
}
```

## 告警示例

当超过阈值时，事件会包含 `alerts` 字段：

```json
{
  "data": {
    "alerts": [
      "温度过高: 87°C",
      "显存使用率过高: 92.5%"
    ]
  },
  "severity": "warn"
}
```
