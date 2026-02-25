# AIOS v1.0 - AI Operating System

**从监控 → 自动修复 → 自我进化**

AIOS 是一个轻量级、零依赖的 AI 操作系统框架，提供完整的可观测性、自动修复和自我进化能力。

---

## 🚀 10秒快速开始

```bash
# 1. 解压（如果是 zip 包）
unzip AIOS-v1.0-demo.zip
cd aios

# 2. 运行演示
python aios.py demo

# 3. 查看系统状态
python aios.py status
```

**就这么简单！零依赖，只需要 Python 3.8+**

---

## 📦 核心功能

### 1. 可观测性（Observability）
- **Tracer** - 分布式追踪（Trace ID + Span ID）
- **Metrics** - 指标收集（Counter/Gauge/Histogram）
- **Logger** - 结构化日志（JSON Lines）

### 2. 自动修复（Reactor）
- 错误模式识别
- Playbook 自动匹配
- 修复验证

### 3. 自我进化（Evolution Engine）
- Agent 性能追踪
- 失败模式分析
- 自动优化配置

### 4. 实时监控（Dashboard）
- 实时指标展示
- 任务追踪时间线
- 进化曲线可视化

---

## 🎯 真实使用场景

### 场景 1: API 健康检查（推荐）

**问题：** 你的 API 服务偶尔会挂掉，需要手动重启

**AIOS 解决方案：**
```bash
python demo_api_health.py
```

**效果：**
- 🔍 每 2 秒自动检查 API 健康状态
- 🚨 连续失败 2 次自动触发告警
- 🔧 自动重启服务（或其他修复操作）
- ✅ 验证修复效果，确认恢复
- 📊 所有事件记录到日志和指标

**输出示例：**
```
[16:54:23] ✅ 检查 #1: 健康
[16:54:25] ✅ 检查 #2: 健康
[16:54:27] ✅ 检查 #3: 健康
[16:54:29] ❌ 检查 #4: 故障
[16:54:31] ❌ 检查 #5: 故障

🚨 检测到连续故障，触发 AIOS 自动修复...
✅ 自动修复成功！

[16:54:34] ✅ 检查 #6: 健康（已恢复）
```

---

### 场景 2: 简单演示（10秒体验）

**快速体验 AIOS 核心功能：**
```bash
python demo_simple.py
```

**展示内容：**
- 任务追踪（Tracer）
- 指标记录（Metrics）
- 结构化日志（Logger）

---

## 🛠️ CLI 命令

```bash
# 系统管理
python aios.py status       # 查看系统状态
python aios.py version      # 显示版本信息

# 演示和测试
python aios.py demo         # 运行真实场景演示（推荐）
python aios.py test         # 运行测试套件
python aios.py benchmark    # 性能基准测试

# 服务管理
python aios.py start        # 启动 AIOS 服务
python aios.py stop         # 停止 AIOS 服务
python aios.py dashboard    # 打开 Dashboard

# 运维工具
python aios.py heartbeat    # 运行心跳检查
python aios.py monitor      # 实时监控（5分钟）
python aios.py analyze      # 性能分析
python aios.py warmup       # 预热组件
```

---

## 💻 API 使用

### 基础用法

```python
from observability import span, METRICS, get_logger

logger = get_logger("MyApp")

# 追踪一个任务
with span("my-task"):
    logger.info("开始执行任务")
    METRICS.inc_counter("tasks.started", 1)
    
    # ... 你的代码 ...
    
    METRICS.inc_counter("tasks.completed", 1)
```

### 指标记录

```python
from observability import METRICS

# Counter（计数器）
METRICS.inc_counter("requests.total", 1, labels={"method": "GET"})

# Gauge（仪表盘）
METRICS.set_gauge("system.cpu", 45.2, labels={"host": "localhost"})

# Histogram（直方图）
METRICS.observe("request.duration", 0.5, labels={"endpoint": "/api"})
```

### 结构化日志

```python
from observability import get_logger

logger = get_logger("MyApp")

logger.info("用户登录", user_id=123, ip="192.168.1.1")
logger.log("ERROR", "数据库连接失败", error="timeout", retry=3)
```

---

## 📊 Dashboard

启动 Dashboard：
```bash
python aios.py dashboard
```

访问 `http://127.0.0.1:9091`

**功能：**
- 实时指标展示（CPU/内存/任务数）
- 任务追踪时间线（Trace ID + Span ID）
- Self-Improving Loop 进化曲线
- 系统健康状态

---

## 📁 项目结构

```
aios/
├── aios.py                 # 统一 CLI 入口
├── demo_api_health.py      # 真实场景演示（API 健康检查）
├── demo_simple.py          # 10秒快速演示
├── observability/          # 可观测性组件
│   ├── tracer.py          # 追踪
│   ├── metrics.py         # 指标
│   └── logger.py          # 日志
├── agent_system/          # Agent 系统
│   ├── auto_dispatcher.py # 自动调度
│   ├── orchestrator.py    # 编排器
│   └── evolution_engine.py # 进化引擎
├── dashboard/             # 实时监控面板
│   ├── index.html
│   └── server.py
└── data/                  # 数据目录
    ├── reports/           # 报告
    ├── evolution/         # 进化记录
    └── metrics.jsonl      # 指标数据
```

---

## 🔧 配置

### 环境变量

```bash
# Windows
set AIOS_LOG_PATH=aios/logs/aios.jsonl
set AIOS_EVENTS_PATH=events.jsonl
set AIOS_DASHBOARD_PORT=9091

# Linux/Mac
export AIOS_LOG_PATH="aios/logs/aios.jsonl"
export AIOS_EVENTS_PATH="events.jsonl"
export AIOS_DASHBOARD_PORT=9091
```

### 配置文件

编辑 `config.yaml`（如果存在）：
```yaml
observability:
  log_level: INFO
  metrics_interval: 60

agent_system:
  max_agents: 15
  idle_timeout: 3600

dashboard:
  port: 9091
  refresh_interval: 5
```

---

## 🧪 测试

```bash
# 需要先安装 pytest（可选）
pip install pytest

# 运行所有测试
python aios.py test

# 或者直接用 pytest
pytest tests/ -v
```

---

## 📈 性能

- **心跳延迟**: ~3ms（比原版快 443 倍）
- **Agent 创建**: 0.3s（比原版快 600 倍）
- **内存占用**: <50MB（零依赖）
- **并发支持**: 1000+ 任务/秒

---

## ❓ 常见问题

### Q: 需要安装依赖吗？
A: **不需要！** AIOS 是零依赖的，只需要 Python 3.8+ 即可。

### Q: 支持哪些 Python 版本？
A: Python 3.8, 3.9, 3.10, 3.11, 3.12 都支持。

### Q: 可以在生产环境使用吗？
A: 可以！AIOS v1.0 已经过充分测试，性能优异。

### Q: 如何集成到我的项目？
A: 只需要导入 `observability` 模块：
```python
from observability import span, METRICS, get_logger
```

### Q: 遇到问题怎么办？
A: 
1. 运行 `python aios.py status` 检查系统状态
2. 查看日志文件 `aios/logs/aios.jsonl`
3. 查看本文档的"使用场景"部分

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 💡 下一步

1. ✅ 运行 `python aios.py demo` 体验真实场景
2. 📖 查看 `demo_api_health.py` 源码学习 API 用法
3. 🌐 启动 `python aios.py dashboard` 查看实时监控
4. 🚀 集成到你的项目中

---

**AIOS v1.0** - 让 AI 系统自己运行、自己看、自己进化！🚀
