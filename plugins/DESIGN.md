# AIOS 插件系统设计

## 目标
- 让 AIOS 可扩展（Sensor、Reactor、Notifier、Dashboard、Integration）
- 插件热加载/卸载
- 插件市场（本地 + 远程）
- 安全沙箱（可选）

## 插件类型

### 1. Sensor 插件（数据采集）
```python
class SensorPlugin(AIOSPlugin):
    def collect(self) -> List[Event]:
        """采集数据，返回事件列表"""
        pass
    
    def interval(self) -> int:
        """采集间隔（秒）"""
        return 60
```

**示例：**
- `gpu_sensor` - GPU 使用率、温度、显存
- `network_sensor` - 网络延迟、丢包率
- `app_sensor` - 应用状态（QQ音乐、LOL）

### 2. Reactor 插件（自动修复）
```python
class ReactorPlugin(AIOSPlugin):
    def match(self, event: Event) -> bool:
        """判断是否匹配此事件"""
        pass
    
    def react(self, event: Event) -> Action:
        """生成修复动作"""
        pass
    
    def verify(self, action: Action) -> bool:
        """验证修复是否成功"""
        pass
```

**示例：**
- `restart_app` - 应用崩溃自动重启
- `clear_cache` - 磁盘满自动清理
- `switch_network` - 网络故障切换备用

### 3. Notifier 插件（通知渠道）
```python
class NotifierPlugin(AIOSPlugin):
    def send(self, message: str, level: str) -> bool:
        """发送通知（info/warn/error/critical）"""
        pass
    
    def supports_rich_text(self) -> bool:
        """是否支持富文本（Markdown/HTML）"""
        return False
```

**示例：**
- `telegram_notifier` - Telegram 通知
- `email_notifier` - 邮件通知
- `voice_notifier` - 语音播报（TTS）

### 4. Dashboard 插件（监控面板）
```python
class DashboardPlugin(AIOSPlugin):
    def render(self) -> str:
        """返回 HTML/JSON"""
        pass
    
    def api_routes(self) -> Dict[str, Callable]:
        """自定义 API 路由"""
        return {}
```

**示例：**
- `system_dashboard` - 系统资源监控
- `agent_dashboard` - Agent 状态面板
- `event_timeline` - 事件时间线

### 5. Integration 插件（第三方集成）
```python
class IntegrationPlugin(AIOSPlugin):
    def on_event(self, event: Event) -> None:
        """事件触发时调用"""
        pass
    
    def webhook(self, data: dict) -> None:
        """接收外部 webhook"""
        pass
```

**示例：**
- `github_integration` - GitHub Issues/PR 同步
- `jira_integration` - Jira 工单同步
- `prometheus_integration` - Prometheus 指标导出

## 插件接口（基类）

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class PluginType(Enum):
    SENSOR = "sensor"
    REACTOR = "reactor"
    NOTIFIER = "notifier"
    DASHBOARD = "dashboard"
    INTEGRATION = "integration"

@dataclass
class PluginMeta:
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    capabilities: List[str]
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None

class AIOSPlugin(ABC):
    """AIOS 插件基类"""
    
    @abstractmethod
    def meta(self) -> PluginMeta:
        """插件元信息"""
        pass
    
    @abstractmethod
    def init(self, config: Dict[str, Any]) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        pass
    
    def on_load(self) -> None:
        """插件加载时调用"""
        pass
    
    def on_unload(self) -> None:
        """插件卸载时调用"""
        pass
    
    def on_event(self, event: "Event") -> None:
        """事件触发时调用（可选）"""
        pass
```

## 插件管理器

```python
class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, AIOSPlugin] = {}
        self.plugin_dir = Path("aios/plugins")
    
    def discover(self) -> List[str]:
        """发现可用插件"""
        pass
    
    def load(self, name: str, config: dict = None) -> bool:
        """加载插件"""
        pass
    
    def unload(self, name: str) -> bool:
        """卸载插件"""
        pass
    
    def reload(self, name: str) -> bool:
        """重载插件"""
        pass
    
    def list(self) -> List[PluginMeta]:
        """列出已加载插件"""
        pass
    
    def get(self, name: str) -> Optional[AIOSPlugin]:
        """获取插件实例"""
        pass
    
    def call(self, name: str, method: str, *args, **kwargs) -> Any:
        """调用插件方法"""
        pass
```

## 插件配置

每个插件有独立的配置文件：`aios/plugins/<name>/config.yaml`

```yaml
# aios/plugins/gpu_sensor/config.yaml
enabled: true
interval: 30  # 采集间隔（秒）
thresholds:
  temperature: 85  # 温度阈值（℃）
  memory_usage: 90  # 显存使用率阈值（%）
  utilization: 95  # GPU 使用率阈值（%）
notify_on_threshold: true
```

## 插件目录结构

```
aios/plugins/
├── __init__.py
├── base.py              # 插件基类
├── manager.py           # 插件管理器
├── loader.py            # 插件加载器
├── registry.py          # 插件注册表
├── DESIGN.md            # 本文档
├── gpu_sensor/          # 示例插件
│   ├── __init__.py
│   ├── plugin.py
│   ├── config.yaml
│   └── README.md
└── telegram_notifier/
    ├── __init__.py
    ├── plugin.py
    ├── config.yaml
    └── README.md
```

## 插件生命周期

```
发现 → 验证 → 加载 → 初始化 → 运行 → 卸载
  ↓      ↓      ↓       ↓       ↓      ↓
discover → validate → load → init → run → unload
```

## 插件市场

### 本地插件
- 放在 `aios/plugins/` 目录
- 自动发现并加载

### 远程插件
- 从 GitHub/PyPI 安装
- `aios plugin install <name>`
- 自动下载到 `aios/plugins/`

### 插件元数据
```json
{
  "name": "gpu_sensor",
  "version": "1.0.0",
  "description": "GPU 监控插件",
  "author": "小九",
  "plugin_type": "sensor",
  "capabilities": ["collect", "threshold_alert"],
  "dependencies": ["pynvml"],
  "repository": "https://github.com/aios-plugins/gpu-sensor",
  "license": "MIT"
}
```

## 安全机制

### 1. 权限控制
```python
class PluginPermissions:
    READ_EVENTS = "read_events"
    WRITE_EVENTS = "write_events"
    EXECUTE_COMMANDS = "execute_commands"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM = "file_system"
```

### 2. 沙箱隔离（可选）
- 使用 `subprocess` 运行插件
- 限制资源使用（CPU、内存、网络）
- 超时保护

### 3. 签名验证
- 官方插件签名
- 第三方插件警告

## CLI 命令

```bash
# 列出所有插件
aios plugin list

# 安装插件
aios plugin install <name>

# 卸载插件
aios plugin uninstall <name>

# 启用/禁用插件
aios plugin enable <name>
aios plugin disable <name>

# 重载插件
aios plugin reload <name>

# 插件健康检查
aios plugin health <name>

# 搜索插件市场
aios plugin search <keyword>

# 发布插件
aios plugin publish <path>
```

## 实现优先级

### Phase 1 - 核心框架（1-2天）
- [x] 插件基类（base.py）
- [ ] 插件管理器（manager.py）
- [ ] 插件加载器（loader.py）
- [ ] CLI 命令（aios plugin）

### Phase 2 - 示例插件（1天）
- [ ] GPU Sensor 插件
- [ ] Telegram Notifier 插件
- [ ] System Dashboard 插件

### Phase 3 - 插件市场（2-3天）
- [ ] 插件注册表（registry.py）
- [ ] 远程安装（GitHub/PyPI）
- [ ] 插件搜索
- [ ] 插件发布

### Phase 4 - 高级特性（可选）
- [ ] 插件沙箱
- [ ] 插件签名
- [ ] 插件依赖管理
- [ ] 插件热重载

## 开放问题

1. **插件配置存储** - YAML vs JSON vs Python dict？
2. **插件通信** - EventBus vs 直接调用？
3. **插件版本管理** - 如何处理版本冲突？
4. **插件依赖** - 如何自动安装依赖？
5. **插件市场托管** - GitHub vs 自建服务器？

---

**下一步：** 实现 Phase 1 核心框架
