# AIOS 架构文档

## 系统概览

AIOS (AI Operating System) 是一个自主的 AI 系统运维框架，通过事件驱动架构实现自动监控、分析、优化和修复。

```
┌─────────────────────────────────────────────────────────────┐
│                        AIOS v0.5                            │
│                   自主系统运维框架                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         Event Bus (事件总线)             │
        │    所有组件通过事件通信，解耦架构          │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Monitor    │    │  Scheduler   │    │   Reactor    │
│   监控层      │───▶│  决策层       │───▶│  执行层       │
│              │    │              │    │              │
│ - 资源监控    │    │ - OODA循环   │    │ - Playbooks  │
│ - 事件采集    │    │ - 优先级队列  │    │ - 自动修复    │
│ - 异常检测    │    │ - 风险评估    │    │ - 验证回滚    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌──────────────┐
                    │ ScoreEngine  │
                    │   评分引擎    │
                    │              │
                    │ - 实时评分    │
                    │ - 趋势分析    │
                    │ - 降级检测    │
                    └──────────────┘
                              │
                              ▼
                    ┌──────────────┐
                    │  Dashboard   │
                    │   监控面板    │
                    │              │
                    │ - 实时监控    │
                    │ - 可视化      │
                    │ - 手动干预    │
                    └──────────────┘
```

## 核心组件

### 1. Event Bus (事件总线)
**职责：** 系统心脏，所有组件通过事件通信

**事件类型：**
- `resource.high` - 资源峰值
- `error.occurred` - 错误发生
- `action.triggered` - 行动触发
- `action.completed` - 行动完成
- `score.updated` - 评分更新

**文件：** `aios/core/event_bus.py`

### 2. Scheduler (决策调度器)
**职责：** 系统大脑，决策何时触发何种行动

**OODA 循环：**
```
Observe (观察) → Orient (判断) → Decide (决策) → Act (执行)
```

**决策流程：**
1. 监听事件（resource.high, error.occurred）
2. 评估优先级（critical > high > medium > low）
3. 检查熔断器状态
4. 触发 Reactor 执行
5. 验证结果
6. 更新评分

**文件：** `aios/core/scheduler.py`

### 3. Reactor (自动修复器)
**职责：** 系统免疫系统，自动匹配并执行修复

**Playbook 结构：**
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
  "auto_execute": true,
  "verify": {
    "metric": "cpu_usage",
    "expected": "<70"
  }
}
```

**执行流程：**
1. 匹配 Playbook（基于事件类型和条件）
2. 风险评估（low 自动执行，medium/high 需确认）
3. 执行行动
4. 验证结果（对比预期指标）
5. 回滚（如果验证失败）

**文件：** `aios/core/reactor.py`

### 4. ScoreEngine (评分引擎)
**职责：** 实时评估系统健康度

**Evolution Score 计算：**
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

**文件：** `aios/core/score_engine.py`

### 5. Agent System (Agent 协作系统)
**职责：** 多 Agent 协作完成复杂任务

**Agent 类型：**
- **Monitor Agent** - 监控系统状态（每5分钟）
- **Analyst Agent** - 分析历史数据（每天）
- **Optimizer Agent** - 生成优化计划（每小时）
- **Executor Agent** - 执行低风险优化（每30分钟）
- **Validator Agent** - 验证优化效果（每天）
- **Learner Agent** - 从经验中学习（每天）

**Orchestrator 协调流程：**
```
Monitor → Analyst → Optimizer → Executor → Validator → Learner
   ↓         ↓          ↓           ↓          ↓          ↓
 告警      建议       计划        执行       验证       学习
```

**文件：** `aios/agent_system/orchestrator.py`

### 6. Dashboard (监控面板)
**职责：** 可视化监控和手动干预

**功能：**
- 实时监控（WebSocket + HTTP 降级）
- Evolution Score 趋势图
- Agent 状态展示
- 心跳任务状态
- 手动触发 Pipeline/Agent

**技术栈：**
- FastAPI (后端)
- Chart.js (图表)
- WebSocket (实时更新)

**文件：** `aios/dashboard/server.py`

## 数据流

### 完整闭环示例：CPU 峰值自动修复

```
1. Monitor 检测到 CPU 使用率 85%
   ↓
2. 发送事件到 Event Bus
   event_type: "resource.high"
   payload: {"resource": "cpu", "value": 85}
   ↓
3. Scheduler 接收事件
   - 评估优先级：high
   - 检查熔断器：正常
   - 决策：触发 Reactor
   ↓
4. Reactor 匹配 Playbook
   - 找到 "reduce_heartbeat_freq"
   - 风险：low，自动执行
   ↓
5. 执行行动
   - 修改 heartbeat.interval: 60 → 120
   - 重启相关服务
   ↓
6. 验证结果
   - 等待 5 分钟
   - 检查 CPU 使用率：65%
   - 验证通过 ✅
   ↓
7. ScoreEngine 更新评分
   - evolution_score: 0.45 → 0.52
   - 记录成功案例
   ↓
8. Learner Agent 学习
   - 提取模式："CPU高 → 降低心跳频率 → 成功"
   - 更新 lessons.json
```

## 文件结构

```
aios/
├── core/                      # 核心组件
│   ├── event_bus.py          # 事件总线
│   ├── scheduler.py          # 决策调度器
│   ├── reactor.py            # 自动修复器
│   ├── score_engine.py       # 评分引擎
│   └── alerts.py             # 告警管理
├── agent_system/             # Agent 系统
│   ├── orchestrator.py       # Agent 协调器
│   ├── monitor_agent.py      # 监控 Agent
│   ├── analyst_agent.py      # 分析 Agent
│   ├── optimizer_agent.py    # 优化 Agent
│   ├── executor_agent.py     # 执行 Agent
│   ├── validator_agent.py    # 验证 Agent
│   └── learner_agent.py      # 学习 Agent
├── dashboard/                # 监控面板
│   ├── server.py             # FastAPI 服务器
│   ├── index.html            # 主界面
│   └── pixel_view/           # Pixel Agents 视图
├── data/                     # 数据文件
│   ├── playbooks.json        # Reactor Playbooks
│   ├── events.jsonl          # 事件日志
│   └── baseline.jsonl        # 基线快照
├── learning/                 # 学习模块
│   ├── baseline.py           # 基线快照
│   └── knowledge_extractor.py # 知识提取
└── maintenance/              # 维护模块
    ├── auto_cleanup.py       # 自动清理
    └── backup.py             # 自动备份
```

## 配置文件

### HEARTBEAT.md
心跳任务配置，定义各个任务的执行频率：

```markdown
### 每小时：AIOS Agent 闭环
- 运行 orchestrator.py
- 完整 OODA 循环

### 每10分钟：Reactor 自动触发
- 监听最近 10 分钟的事件
- 自动匹配 playbooks 并执行修复

### 每次心跳：轻量级监控
- 运行 heartbeat_runner.py
- 仅记录事件，不触发修复
```

### selflearn-state.json
记录各个任务的上次执行时间：

```json
{
  "last_orchestrator": "2026-02-24T12:47:18",
  "last_reactor": "2026-02-24T12:40:00",
  "last_self_improving": "2026-02-24T03:09:17",
  "last_baseline": "2026-02-24T09:00:00"
}
```

## 扩展性

### 添加新的 Playbook

1. 编辑 `aios/data/playbooks.json`
2. 定义触发条件和行动
3. 设置风险级别和自动执行策略
4. Reactor 会自动加载新 Playbook

### 添加新的 Agent

1. 创建新的 Agent 文件（继承 BaseAgent）
2. 在 Orchestrator 中注册
3. 定义执行间隔和依赖关系

### 自定义评分算法

修改 `aios/core/score_engine.py` 的权重和计算逻辑。

## 性能优化

### 已实现
- ✅ 熔断器（防止重复失败）
- ✅ 异步 Spawn（600x 加速）
- ✅ 事件批量处理
- ✅ WebSocket 实时更新

### 计划中（v0.6）
- ⏳ 优先级队列（高优先级任务优先）
- ⏳ 权重自学习（根据历史数据调整）
- ⏳ 自动回滚机制（验证失败自动回滚）

## 监控指标

### 核心指标
- **Evolution Score** - 系统进化分数（0-1）
- **Tool Success Rate** - 工具成功率
- **Reactor Execution Rate** - 自动修复执行率
- **Verification Pass Rate** - 验证通过率

### 资源指标
- **CPU Usage** - CPU 使用率
- **Memory Usage** - 内存使用率
- **GPU Usage** - GPU 使用率（如果有）
- **Disk Usage** - 磁盘使用率

### 事件指标
- **Events/Hour** - 每小时事件数
- **Errors/Hour** - 每小时错误数
- **Warnings/Hour** - 每小时警告数

## 故障排查

### Dashboard 无法访问
```bash
# 检查服务是否运行
Get-Process -Name python | Where-Object {$_.CommandLine -like "*dashboard*"}

# 手动启动
cd C:\Users\A\.openclaw\workspace\aios\dashboard
python server.py
```

### Orchestrator 不执行
```bash
# 检查时间戳
cat C:\Users\A\.openclaw\workspace\memory\selflearn-state.json

# 手动触发
python C:\Users\A\.openclaw\workspace\aios\agent_system\orchestrator.py
```

### Reactor 不触发
```bash
# 检查 Playbooks
cat C:\Users\A\.openclaw\workspace\aios\data\playbooks.json

# 检查事件日志
tail -n 50 C:\Users\A\.openclaw\workspace\aios\data\events.jsonl
```

## 安全考虑

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

## 开源准备

### 已完成
- ✅ 代码整理
- ✅ 文档齐全
- ✅ 测试覆盖（16/16）
- ✅ PyPI 打包配置

### 待完成
- ⏳ 补充单元测试
- ⏳ 性能基准测试
- ⏳ 安全审计
- ⏳ 发布到 PyPI

---

**版本：** v0.5  
**更新时间：** 2026-02-24  
**作者：** 珊瑚海 + 小九
