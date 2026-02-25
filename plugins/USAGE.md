# AIOS 插件系统 v0.1 - 使用指南

## 🚀 快速开始

### 1. 启动 Dashboard

```bash
cd C:\Users\A\.openclaw\workspace\aios
python start_dashboard.py
```

访问：http://localhost:8765

### 2. 运行快速演示

```bash
python -X utf8 demo_quick.py
```

### 3. 查看插件状态

```bash
python __main__.py plugin list
python __main__.py plugin health
```

## 📊 Dashboard 查看插件

Dashboard 已集成插件状态，访问 http://localhost:8765 可以看到：

- **插件总数** - 已加载的插件数量
- **插件状态** - enabled/failed
- **插件统计** - 调用次数、成功率、平均耗时
- **最近错误** - 插件执行失败的错误信息

## 🎯 使用场景

### 场景1：监控系统资源

```python
from plugins.manager import get_manager

manager = get_manager()
manager.load("builtin/sensor_resource")

# Sensor 会采集 CPU、内存、磁盘数据
sensor = manager.get("builtin/sensor_resource")
events = sensor.collect()
print(events)
```

### 场景2：自动通知告警

```python
from plugins.manager import get_manager
from plugins.eventbus import get_bus

manager = get_manager()
bus = get_bus()

# 加载通知插件
manager.load("builtin/notifier_console")

# 发布告警事件
bus.publish("alert.high_cpu", {
    "message": "CPU 使用率过高: 95%",
    "severity": "warn"
})
# → 自动打印到控制台
```

### 场景3：自动修复错误

```python
from plugins.manager import get_manager
from plugins.eventbus import get_bus

manager = get_manager()
bus = get_bus()

# 加载修复插件
manager.load("builtin/reactor_demo")

# 发布错误事件
bus.publish("event.provider.error", {
    "provider": "openai",
    "error": "rate_limit",
    "category": "resource_error",
    "severity": "error",
    "data": {"error": "Rate limit exceeded"}
})
# → 自动触发修复
```

## 🔧 CLI 命令

### 发现插件

```bash
python __main__.py plugin discover
```

输出：
```
发现 6 个插件:
  [ ] aram
  [ ] gateway
  [ ] gpu_sensor
  [✓] builtin/notifier_console
  [✓] builtin/reactor_demo
  [✓] builtin/sensor_resource
```

### 加载插件

```bash
python __main__.py plugin load builtin/sensor_resource
```

### 列出已加载插件

```bash
python __main__.py plugin list
```

输出：
```
  ✓ sensor_resource v1.0.0 (sensor)
     系统资源监控（CPU、内存、磁盘）
  ✓ notifier_console v1.0.0 (notifier)
     控制台通知插件（打印告警到终端）
  ✓ reactor_demo v1.0.0 (reactor)
     演示 Reactor 插件（自动修复示例）
```

### 健康检查

```bash
python __main__.py plugin health
```

输出：
```
  ✓ builtin/sensor_resource: ok - 资源监控正常
  ✓ builtin/notifier_console: ok - 控制台通知正常
  ✓ builtin/reactor_demo: ok - Demo Reactor 正常，监听 3 个类别
```

### 卸载插件

```bash
python __main__.py plugin unload builtin/sensor_resource
```

### 重载插件

```bash
python __main__.py plugin reload builtin/sensor_resource
```

### 启用/禁用插件

```bash
python __main__.py plugin enable builtin/sensor_resource
python __main__.py plugin disable builtin/sensor_resource
```

## 📝 创建自定义插件

### 1. 创建插件目录

```bash
mkdir -p aios/plugins/my_plugin
```

### 2. 编写插件代码

```python
# aios/plugins/my_plugin/plugin.py
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).parent.parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from plugins.base import SensorPlugin, PluginMeta, PluginType

class MyPlugin(SensorPlugin):
    def meta(self) -> PluginMeta:
        return PluginMeta(
            name="my_plugin",
            version="1.0.0",
            description="我的自定义插件",
            author="你的名字",
            plugin_type=PluginType.SENSOR,
        )
    
    def subscriptions(self) -> list:
        """订阅事件（可选）"""
        return ["event.*"]
    
    def init(self, config: dict) -> bool:
        print("插件初始化")
        return True
    
    def collect(self) -> list:
        """采集数据"""
        return [{
            "timestamp": int(time.time()),
            "layer": "KERNEL",
            "category": "custom",
            "data": {"value": 42}
        }]
    
    def on_event(self, event: dict):
        """处理事件"""
        print(f"收到事件: {event}")
    
    def health_check(self) -> dict:
        return {"status": "ok"}

# 导出插件类
PLUGIN_CLASS = MyPlugin
```

### 3. 创建配置文件

```yaml
# aios/plugins/my_plugin/config.yaml
enabled: true
interval: 60
```

### 4. 加载插件

```bash
python __main__.py plugin load my_plugin
```

## 🎯 事件订阅模式

### 通配符订阅

```python
def subscriptions(self) -> list:
    return [
        "event.*",              # 所有事件
        "event.provider.*",     # Provider 相关事件
        "event.*error*",        # 所有错误事件
        "alert.*",              # 所有告警
    ]
```

### 常用 Topic

- `event.kernel.resource_snapshot` - 资源快照
- `event.provider.error` - Provider 错误
- `event.task.failed` - 任务失败
- `event.network.error` - 网络错误
- `alert.high_cpu` - CPU 告警
- `alert.high_memory` - 内存告警

## 📊 插件统计

插件管理器自动统计每个插件的：

- **调用次数** - 处理了多少个事件
- **成功次数** - 成功处理的事件数
- **失败次数** - 处理失败的事件数
- **平均耗时** - 每次处理的平均时间（EMA 平滑）
- **最近错误** - 最后一次失败的错误信息

查看统计：

```python
from plugins.manager import get_manager

manager = get_manager()
stats = manager.plugin_stats

for name, stat in stats.items():
    print(f"{name}:")
    print(f"  调用: {stat['calls']}")
    print(f"  成功: {stat['ok']}")
    print(f"  失败: {stat['fail']}")
    print(f"  平均耗时: {stat['avg_ms']:.2f}ms")
```

## 🔒 安全机制

### 错误隔离

单个插件错误不会拖垮整个系统：

```python
# 插件抛出异常
def on_event(self, event):
    raise Exception("插件错误")

# → 错误被捕获，记录到 plugin_stats
# → 其他插件继续正常工作
```

### 性能监控

自动监控插件性能：

```python
# 如果插件处理时间过长
def on_event(self, event):
    time.sleep(10)  # 10秒

# → 自动记录到 avg_ms
# → Dashboard 可以看到慢插件
```

## 🎉 下一步

1. **对接现有系统** - 将插件系统集成到 AIOS 核心
2. **写更多插件** - Telegram Notifier、Network Sensor 等
3. **插件市场** - 远程安装、搜索、发布

---

**提示：** 插件系统已就绪，可以开始使用！访问 http://localhost:8765 查看 Dashboard。
