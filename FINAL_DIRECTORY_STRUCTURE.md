# AIOS 完整目录结构（可观测 + 可交付版）

```
C:\Users\A\.openclaw\workspace\
├── aios/
│   ├── __init__.py
│   ├── __main__.py                          # 主入口（待整合）
│   │
│   ├── observability/                       # 🔥 可观测层（新增）
│   │   ├── __init__.py
│   │   ├── tracer.py                        # 分布式追踪
│   │   ├── metrics.py                       # 实时指标
│   │   ├── logger.py                        # 结构化日志
│   │   ├── traces/                          # Trace 文件
│   │   │   └── trace_*.json
│   │   ├── metrics/                         # Metrics 快照
│   │   │   └── metrics_*.json
│   │   └── logs/                            # 日志文件
│   │       └── *.log
│   │
│   ├── dashboard/                           # 🔥 Dashboard（新增）
│   │   ├── index.html                       # 实时看板
│   │   └── dashboard_server.py              # HTTP 服务器
│   │
│   ├── demo/                                # 🔥 演示脚本（新增）
│   │   └── README.md                        # 快速开始指南
│   │
│   ├── agent_system/                        # Agent 系统
│   │   ├── auto_dispatcher.py               # 原版
│   │   ├── auto_dispatcher_v2.py            # 🔥 可观测增强版（新增）
│   │   ├── orchestrator.py
│   │   ├── self_improving_loop.py
│   │   ├── evolution_engine.py
│   │   ├── circuit_breaker.py
│   │   ├── task_queue.jsonl                 # 任务队列
│   │   ├── spawn_requests.jsonl             # Spawn 请求
│   │   ├── dispatcher.log                   # 旧版日志
│   │   └── data/
│   │       ├── agents.jsonl                 # Agent 配置
│   │       ├── agent_configs.json
│   │       ├── traces/
│   │       │   └── agent_traces.jsonl
│   │       ├── reports/
│   │       │   └── cycle_*.json
│   │       └── evolution/
│   │           └── evolution_history.jsonl
│   │
│   ├── core/                                # 核心模块
│   │   ├── event_bus.py
│   │   ├── event.py
│   │   ├── event_store.py
│   │   ├── scheduler.py
│   │   ├── reactor.py
│   │   └── score_engine.py
│   │
│   ├── learning/                            # 学习模块
│   │   ├── baseline.py
│   │   ├── reactor.py
│   │   └── playbook_manager.py
│   │
│   ├── data/                                # 数据文件
│   │   ├── playbooks.json                   # Playbook 规则
│   │   └── playbook_stats.json
│   │
│   ├── logs/                                # 🔥 统一日志目录（新增）
│   │   └── aios.jsonl                       # 结构化日志
│   │
│   ├── demo_full_cycle.py                   # 原版 Demo
│   ├── demo_full_cycle_v2.py                # 🔥 可观测增强版（新增）
│   ├── reactor_auto_trigger.py
│   ├── heartbeat_runner_optimized.py
│   │
│   ├── CAPABILITIES.md                      # 🔥 能力说明（新增）
│   ├── QUICK_START_REPORT.md                # 🔥 快速验证报告（新增）
│   ├── REACTOR_DEMO_REPORT.md               # 🔥 Reactor 演示报告（新增）
│   ├── SELF_IMPROVING_DEMO_REPORT.md        # 🔥 Self-Improving 报告（新增）
│   ├── OBSERVABILITY_INJECTION_REPORT.md    # 🔥 可观测注入报告（新增）
│   └── AUTO_DISPATCHER_INJECTION_COMPLETE.md # 🔥 注入完成说明（新增）
│
├── events.jsonl                             # 🔥 统一事件流（新增）
│
├── memory/                                  # 记忆系统
│   ├── YYYY-MM-DD.md                        # 每日日志
│   ├── lessons.json                         # 教训库
│   ├── corrections.json
│   └── selflearn-state.json
│
├── smoke_test.py                            # 🔥 可观测层测试（新增）
├── debug_trace.py                           # 🔥 Trace 调试（新增）
│
├── AGENTS.md                                # Agent 指南
├── SOUL.md                                  # 个性定义
├── USER.md                                  # 用户信息
├── IDENTITY.md                              # 身份信息
├── TOOLS.md                                 # 工具配置
├── HEARTBEAT.md                             # 心跳任务
└── MEMORY.md                                # 长期记忆
```

---

## 🔥 新增文件清单

### 可观测层（7 个文件）
1. `aios/observability/__init__.py` - 统一入口
2. `aios/observability/tracer.py` - 分布式追踪
3. `aios/observability/metrics.py` - 实时指标
4. `aios/observability/logger.py` - 结构化日志
5. `aios/logs/aios.jsonl` - 统一日志文件
6. `events.jsonl` - 统一事件流
7. `aios/observability/traces/` - Trace 文件目录

### Dashboard（2 个文件）
8. `aios/dashboard/index.html` - 实时看板
9. `aios/dashboard/dashboard_server.py` - HTTP 服务器

### 演示脚本（2 个文件）
10. `aios/demo_full_cycle_v2.py` - 可观测增强版 Demo
11. `aios/demo/README.md` - 快速开始指南

### 注入版本（1 个文件）
12. `aios/agent_system/auto_dispatcher_v2.py` - 可观测增强版

### 测试脚本（2 个文件）
13. `smoke_test.py` - 可观测层测试
14. `debug_trace.py` - Trace 调试

### 文档（6 个文件）
15. `aios/CAPABILITIES.md` - 能力说明
16. `aios/QUICK_START_REPORT.md` - 快速验证报告
17. `aios/REACTOR_DEMO_REPORT.md` - Reactor 演示报告
18. `aios/SELF_IMPROVING_DEMO_REPORT.md` - Self-Improving 报告
19. `aios/OBSERVABILITY_INJECTION_REPORT.md` - 可观测注入报告
20. `aios/AUTO_DISPATCHER_INJECTION_COMPLETE.md` - 注入完成说明

---

## 📊 文件统计

- **总新增文件：** 20 个
- **可观测层：** 7 个
- **Dashboard：** 2 个
- **演示脚本：** 2 个
- **注入版本：** 1 个
- **测试脚本：** 2 个
- **文档：** 6 个

---

## 🚀 快速开始

### 1. 测试可观测层
```bash
cd C:\Users\A\.openclaw\workspace
python smoke_test.py
```

### 2. 运行完整 Demo
```bash
python aios\demo_full_cycle_v2.py
```

### 3. 启动 Dashboard
```bash
python aios\dashboard\dashboard_server.py
# 访问 http://localhost:8080
```

### 4. 替换 Dispatcher（生产环境）
```bash
# 备份
cp aios\agent_system\auto_dispatcher.py aios\agent_system\auto_dispatcher_backup.py

# 替换
cp aios\agent_system\auto_dispatcher_v2.py aios\agent_system\auto_dispatcher.py
```

---

## ✅ 验收标准

1. **✓ 可观测层工作** - smoke_test.py 通过
2. **✓ Demo 运行成功** - demo_full_cycle_v2.py 完成
3. **✓ Dashboard 可访问** - http://localhost:8080 显示数据
4. **✓ 日志有 trace_id** - aios/logs/aios.jsonl 格式正确
5. **✓ 事件流正常** - events.jsonl 有数据
6. **✓ 指标可导出** - METRICS.snapshot() 工作

---

**🎉 可观测 + 可交付 全部封顶！**
