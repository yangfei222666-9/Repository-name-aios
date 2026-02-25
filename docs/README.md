# AIOS 文档中心

欢迎来到 AIOS (AI Operating System) 文档中心！

## 📚 文档导航

### 新手入门
- **[快速开始](EXAMPLES.md#快速开始)** - 5分钟上手 AIOS
- **[使用示例](EXAMPLES.md)** - 常见场景和解决方案

### 深入理解
- **[架构文档](ARCHITECTURE.md)** - 系统设计和核心组件
- **[数据流](ARCHITECTURE.md#数据流)** - 完整闭环示例

### 运维指南
- **[监控最佳实践](EXAMPLES.md#监控最佳实践)** - 日常运维建议
- **[故障排查](ARCHITECTURE.md#故障排查)** - 常见问题解决
- **[性能调优](EXAMPLES.md#性能调优)** - 优化系统性能

### 高级用法
- **[自定义 Playbook](EXAMPLES.md#自定义-playbook)** - 扩展自动修复能力
- **[集成到 OpenClaw](EXAMPLES.md#集成到-openclaw)** - 心跳任务配置

## 🚀 快速链接

| 功能 | 文档 | 文件 |
|------|------|------|
| 启动 Dashboard | [使用示例](EXAMPLES.md#1-启动-dashboard) | `aios/dashboard/server.py` |
| 手动触发 Orchestrator | [使用示例](EXAMPLES.md#2-手动触发-orchestrator) | `aios/agent_system/orchestrator.py` |
| 查看 Evolution Score | [使用示例](EXAMPLES.md#3-查看-evolution-score) | `aios/learning/baseline.py` |
| CPU 使用率过高 | [场景 1](EXAMPLES.md#场景-1cpu-使用率过高) | 自动修复 |
| 工具调用失败率高 | [场景 2](EXAMPLES.md#场景-2工具调用失败率高) | 手动干预 |
| Agent 创建失败 | [场景 3](EXAMPLES.md#场景-3agent-创建失败) | 熔断器重置 |
| 系统降级 | [场景 4](EXAMPLES.md#场景-4系统降级) | 健康检查 |

## 📊 核心概念

### Evolution Score
系统进化分数，综合评估系统自我改进能力（0-1）。

**计算公式：**
```
score = health * 0.4 +           # 工具成功率
        efficiency * 0.25 +      # 效率（延迟）
        stability * 0.25 +       # 稳定性（错误率）
        resource_headroom * 0.1  # 资源余量
```

**分级：**
- `healthy` (≥0.7) - 系统健康
- `ok` (0.5-0.7) - 正常运行
- `degraded` (0.3-0.5) - 性能降级
- `critical` (<0.3) - 需要人工介入

### OODA 循环
Scheduler 的决策流程：

```
Observe (观察) → Orient (判断) → Decide (决策) → Act (执行)
```

### Playbook
Reactor 的自动修复脚本，定义触发条件、行动和验证逻辑。

**示例：**
```json
{
  "id": "reduce_heartbeat_freq",
  "trigger": {
    "event_type": "resource.high",
    "conditions": {"resource": "cpu", "threshold": 80}
  },
  "actions": [
    {"type": "config.update", "path": "heartbeat.interval", "value": 120}
  ],
  "risk": "low",
  "auto_execute": true
}
```

## 🏗️ 系统架构

```
Event Bus (事件总线)
    │
    ├─→ Monitor (监控层) ─→ 资源监控、事件采集、异常检测
    │
    ├─→ Scheduler (决策层) ─→ OODA循环、优先级队列、风险评估
    │
    ├─→ Reactor (执行层) ─→ Playbooks、自动修复、验证回滚
    │
    ├─→ ScoreEngine (评分引擎) ─→ 实时评分、趋势分析、降级检测
    │
    └─→ Dashboard (监控面板) ─→ 实时监控、可视化、手动干预
```

详见 [架构文档](ARCHITECTURE.md)。

## 🔧 常用命令

```bash
# 启动 Dashboard
cd aios/dashboard && python server.py

# 手动触发 Orchestrator
python aios/agent_system/orchestrator.py

# 查看 Evolution Score
python aios/learning/baseline.py snapshot

# 健康检查
python aios/maintenance/health_check.py

# 自动清理
python aios/maintenance/auto_cleanup.py

# 备份数据
python aios/maintenance/backup.py
```

## 📈 监控指标

| 指标 | 说明 | 阈值 |
|------|------|------|
| Evolution Score | 系统进化分数 | ≥0.5 |
| Tool Success Rate | 工具成功率 | ≥80% |
| Reactor Execution Rate | 自动修复执行率 | ≥50% |
| CPU Usage | CPU 使用率 | <80% |
| Memory Usage | 内存使用率 | <85% |
| Errors/Hour | 每小时错误数 | <10 |

## 🛡️ 安全机制

### 风险分级
- **low** - 自动执行（如：调整心跳频率）
- **medium** - 需要确认（如：重启服务）
- **high** - 需要人工审核（如：修改核心配置）

### 熔断机制
- 同一 Playbook 24h 内最多执行 3 次
- 失败 3 次后自动熔断，5 分钟后恢复

### 回滚机制
- 所有配置修改前自动备份
- 验证失败自动回滚到上一个稳定状态

## 🤝 贡献指南

欢迎贡献代码、文档或反馈问题！

- 提交 Issue：报告 bug 或提出功能建议
- 提交 PR：改进代码或文档
- 分享经验：在社区分享你的使用经验

## 📝 更新日志

### v0.5 (2026-02-24)
- ✅ 完整闭环（Monitor → Scheduler → Reactor → ScoreEngine）
- ✅ Dashboard 实时监控
- ✅ Agent System 协作
- ✅ 心跳任务状态显示
- ✅ Orchestrator 时间戳追踪

### v0.4 (2026-02-22)
- ✅ 插件系统
- ✅ Dashboard v1.0

### v0.3 (2026-02-20)
- ✅ 感知层（Sensors + Dispatcher）

### v0.2 (2026-02-19)
- ✅ 5层事件架构
- ✅ insight/reflect 分析

## 📞 联系方式

- **作者：** 珊瑚海 + 小九
- **版本：** v0.5
- **更新时间：** 2026-02-24

---

**开始使用：** [快速开始](EXAMPLES.md#快速开始)  
**深入学习：** [架构文档](ARCHITECTURE.md)  
**遇到问题：** [故障排查](ARCHITECTURE.md#故障排查)
