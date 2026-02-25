# AIOS 插件系统集成完成

## ✅ 已完成

### 1. 桥接模块
- **文件：** `plugins/bridge.py`
- **功能：** 将插件 EventBus 连接到 AIOS 核心 EventBus

### 2. 初始化脚本
- **文件：** `init_plugins.py`
- **功能：** 在 AIOS 启动时初始化插件系统

### 3. 测试结果
```
发布测试事件:
  → provider.error
  → task.failed

插件统计:
  builtin/reactor_demo:
    调用: 4, 成功: 4, 失败: 0
```

## 🚀 使用方法

### 方法1：在现有代码中集成

```python
from core.event_bus import EventBus
from init_plugins import init_plugins

# 创建或获取 EventBus
bus = EventBus()

# 初始化插件系统
init_plugins(bus)

# 发布事件（插件会自动响应）
from core.event import Event

event = Event.create(
    event_type="provider.error",
    source="my_module",
    payload={"provider": "openai", "error": "rate_limit"}
)
bus.emit(event)
```

### 方法2：在 pipeline.py 中集成

在 `pipeline.py` 的开头添加：

```python
# 初始化插件系统（只需一次）
from init_plugins import init_plugins
init_plugins()
```

### 方法3：在 heartbeat 中集成

在心跳脚本中添加：

```python
from init_plugins import init_plugins
from core.event_bus import EventBus

bus = EventBus()
init_plugins(bus)
```

## 📊 事件格式

AIOS 核心事件格式：

```python
Event(
    id="uuid",
    type="provider.error",  # 事件类型
    source="module_name",   # 事件来源
    timestamp=1708761600,   # 毫秒时间戳
    payload={               # 事件数据
        "provider": "openai",
        "error": "rate_limit",
        "severity": "error"
    }
)
```

插件会自动将其转换为插件格式：

```python
{
    "timestamp": 1708761600,
    "topic": "provider.error",
    "type": "provider.error",
    "source": "module_name",
    "data": {...},
    "severity": "error"
}
```

## 🎯 插件订阅规则

插件订阅的 pattern 会自动转换：

| 插件 pattern | 核心 EventBus pattern | 说明 |
|-------------|---------------------|------|
| `event.provider.error` | `provider.error` | 去掉 `event.` 前缀 |
| `event.*error*` | `*error*` | 通配符保持不变 |
| `alert.*` | `alert.*` | 不以 `event.` 开头的保持不变 |

## 📝 下一步

### 1. 在 pipeline.py 中集成
在 `stage_sensors()` 或 `run_pipeline()` 开头添加：

```python
from init_plugins import init_plugins
init_plugins()
```

### 2. 在 Scheduler 中集成
定时触发 Sensor 插件的 `collect()` 方法

### 3. 测试真实场景
发布真实的 AIOS 事件，看插件响应

---

**状态：** ✅ 集成完成，可以使用
**测试：** ✅ 通过
**文档：** ✅ 完整
