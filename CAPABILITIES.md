# AIOS 核心能力实战指南

## 1. 给它任务 → 自动路由

### 怎么用

**方式 1：直接写入队列文件**
```bash
# 写入任务到队列
echo '{"type": "code", "description": "重构 scheduler.py，提取重复逻辑", "priority": "high"}' >> aios/agent_system/task_queue.jsonl
echo '{"type": "analysis", "description": "分析最近7天的失败事件，找出根因", "priority": "normal"}' >> aios/agent_system/task_queue.jsonl
echo '{"type": "monitor", "description": "检查磁盘使用率，清理临时文件", "priority": "low"}' >> aios/agent_system/task_queue.jsonl
```

**方式 2：通过 Python API**
```python
from aios.agent_system.auto_dispatcher import AutoDispatcher
from pathlib import Path

dispatcher = AutoDispatcher(Path.home() / ".openclaw" / "workspace")

# 代码任务
dispatcher.enqueue_task({
    "type": "code",
    "message": "重构 scheduler.py，提取重复逻辑",
    "priority": "high"
})

# 分析任务
dispatcher.enqueue_task({
    "type": "analysis",
    "message": "分析最近7天的失败事件，找出根因",
    "priority": "normal"
})

# 监控任务
dispatcher.enqueue_task({
    "type": "monitor",
    "message": "检查磁盘使用率，清理临时文件",
    "priority": "low"
})
```

### 路由规则

| 任务类型 | 路由到 | 模型 | 擅长 |
|---------|--------|------|------|
| `code` | coder Agent | claude-opus-4-5 | 写代码、重构、修复 bug |
| `analysis` | analyst Agent | claude-sonnet-4-5 | 分析数据、生成报告 |
| `monitor` | monitor Agent | claude-sonnet-4-5 | 监控系统、检查资源 |
| `research` | researcher Agent | claude-sonnet-4-5 | 调研技术、收集信息 |
| `design` | designer Agent | claude-opus-4-5 | 架构设计、方案评审 |
| `test` | tester Agent | claude-sonnet-4-5 | 测试、验证 |
| `document` | documenter Agent | claude-sonnet-4-5 | 写文档、注释 |
| `debug` | debugger Agent | claude-opus-4-5 | 调试、定位问题 |

### 优先级策略

- **high** - 立即处理（插队）
- **normal** - 正常处理（FIFO）
- **low** - 延迟处理（队列空闲时）

### 自动处理

- **心跳时自动处理队列**（最多 5 个任务/次）
- **失败自动重试**（最多 3 次，指数退避：2^n 分钟）
- **超时自动熔断**（3 次失败 → 5 分钟冷却）

### 查看状态

```bash
python aios/agent_system/auto_dispatcher.py status
```

输出示例：
```
Auto Dispatcher Status
  Queue size: 3
  Event subscriptions: 3
  Last scheduled tasks:
    - daily_code_review: 2026-02-24T09:00:00
    - weekly_performance: 2026-02-23T09:00:00
  Circuit Breaker:
    - code: 🟢 HEALTHY (failures: 0, retry: 0s)
    - analysis: 🟢 HEALTHY (failures: 0, retry: 0s)
  Self-Improving Loop:
    - Total agents: 9
    - Total improvements: 2
    - Improved agents: coder-dispatcher, analyst-dispatcher
```

---

## 2. 分析代码、监控系统、生成报告

### 代码分析

**分析代码异味**
```json
{
  "type": "code",
  "message": "分析 aios/core/ 目录，找出代码异味（重复代码、过长函数、循环依赖）",
  "priority": "normal"
}
```

**检查测试覆盖率**
```json
{
  "type": "code",
  "message": "检查 agent_system/ 的测试覆盖率，生成缺失测试清单",
  "priority": "normal"
}
```

### 系统监控

**资源峰值告警**
```json
{
  "type": "monitor",
  "message": "检查最近 1 小时的资源峰值，生成告警报告",
  "priority": "high"
}
```

**性能瓶颈分析**
```json
{
  "type": "monitor",
  "message": "分析 events.jsonl 最慢的 10 个操作，给出优化建议",
  "priority": "normal"
}
```

### 报告生成

**健康报告**
```json
{
  "type": "analysis",
  "message": "生成本周 AIOS 健康报告（Evolution Score 趋势、失败率、优化建议）",
  "priority": "normal"
}
```

**Playbook 效果分析**
```json
{
  "type": "analysis",
  "message": "分析 playbook_stats.json，找出成功率最低的 5 个 Playbook",
  "priority": "normal"
}
```

### 输出位置

- **报告：** `aios/agent_system/data/reports/`
- **日志：** `aios/agent_system/dispatcher.log`
- **结果：** `aios/agent_system/spawn_results.jsonl`

### 实战示例

```bash
# 1. 创建分析任务
echo '{"type": "analysis", "message": "分析最近 24 小时的慢操作（>5s），找出瓶颈", "priority": "high"}' >> aios/agent_system/task_queue.jsonl

# 2. 等待心跳处理（或手动触发）
python aios/agent_system/auto_dispatcher.py heartbeat

# 3. 查看结果
cat aios/agent_system/spawn_results.jsonl | tail -1 | jq .
```

---

## 3. 观察自动改进（Self-Improving Loop）

### 工作原理

```
执行任务 → 记录结果 → 分析失败 → 生成建议 → 自动应用 → 验证效果 → 更新配置
```

### 触发条件

| Agent 类型 | 触发条件 |
|-----------|---------|
| 高频任务 | 失败 ≥3 次 |
| 中频任务 | 失败 ≥3 次 |
| 低频任务 | 失败 ≥2 次 |
| 关键任务 | 失败 1 次立即触发 |

### 自动改进类型

1. **超时调整** - 任务经常超时 → 增加 timeout
2. **优先级调整** - 任务经常被跳过 → 提高 priority
3. **请求频率** - 任务经常失败 → 降低并发数
4. **模型切换** - 任务质量不佳 → 切换到更强模型（需确认）

### 查看改进历史

```bash
# 查看所有 Agent 的改进统计
python aios/agent_system/auto_dispatcher.py status

# 输出示例：
# Self-Improving Loop:
#   - Total agents: 9
#   - Total improvements: 2
#   - Improved agents: coder-dispatcher, analyst-dispatcher
```

### 改进报告位置

- `aios/agent_system/data/reports/cycle_*.json`
- 包含：改进前后对比、效果验证、回滚记录

### 实战示例

```bash
# 1. 故意触发失败（模拟）
for i in {1..3}; do
  echo '{"type": "code", "message": "执行一个会超时的任务", "priority": "high"}' >> aios/agent_system/task_queue.jsonl
done

# 2. 等待心跳处理
python aios/agent_system/auto_dispatcher.py heartbeat

# 3. 查看改进日志
tail -20 aios/agent_system/data/loop.log | jq .

# 4. 查看改进报告
ls -lt aios/agent_system/data/reports/cycle_*.json | head -1 | xargs cat | jq .
```

---

## 4. 从失败中学习

### 学习机制（4 层）

#### Level 1 - 熔断器（立即生效）

- **触发条件：** 同一操作 30 分钟内失败 ≥3 次
- **动作：** 自动熔断
- **恢复：** 1 小时后自动恢复
- **状态文件：** `aios/agent_system/circuit_breaker_state.json`

```bash
# 查看熔断器状态
cat aios/agent_system/circuit_breaker_state.json | jq .
```

#### Level 2 - Playbook 自动修复（10 分钟）

- **监听：** 错误事件
- **匹配：** Playbook 规则
- **执行：** 自动修复（如：清理缓存、重启服务、降低频率）
- **验证：** 检查修复效果

```bash
# 查看 Playbook 统计
cat aios/data/playbook_stats.json | jq '.[] | select(.success_rate < 0.5)'
```

#### Level 3 - 教训库（每天）

- **提取：** 重复错误模式（≥3 次）
- **追加：** `memory/lessons.json`
- **应用：** 下次遇到相同错误 → 直接应用教训

```bash
# 查看教训库
cat memory/lessons.json | jq '.[] | select(.status=="verified")'
```

#### Level 4 - Agent 进化（每天）

- **分析：** Evolution Engine 分析失败模式
- **生成：** Prompt 补丁（如：增加错误处理提示）
- **应用：** 自动应用低风险改进
- **确认：** 中高风险改进需人工确认

```bash
# 查看进化历史
cat aios/agent_system/data/evolution/evolution_history.jsonl | tail -10 | jq .
```

### 学习成果查看

```bash
# 1. 教训库（已验证的教训）
cat memory/lessons.json | jq '.[] | select(.status=="verified")'

# 2. Playbook 统计（成功率 <50% 的规则）
cat aios/data/playbook_stats.json | jq '.[] | select(.success_rate < 0.5)'

# 3. 进化历史（最近 10 条）
cat aios/agent_system/data/evolution/evolution_history.jsonl | tail -10 | jq .

# 4. 改进循环日志
tail -50 aios/agent_system/data/loop.log | jq 'select(.level=="success")'
```

---

## 实战场景

### 场景 1：代码质量检查

```bash
# 1. 创建任务
echo '{"type": "code", "message": "检查 aios/core/event_bus.py 的代码质量，生成改进建议", "priority": "high"}' >> aios/agent_system/task_queue.jsonl

# 2. 触发处理
python aios/agent_system/auto_dispatcher.py heartbeat

# 3. 查看报告
ls -lt aios/agent_system/data/reports/ | head -1 | xargs cat | jq .
```

### 场景 2：性能优化

```bash
# 1. 创建任务
echo '{"type": "analysis", "message": "分析最近 24 小时的慢操作（>5s），找出瓶颈", "priority": "high"}' >> aios/agent_system/task_queue.jsonl

# 2. 触发处理
python aios/agent_system/auto_dispatcher.py heartbeat

# 3. 查看优化建议
cat aios/agent_system/spawn_results.jsonl | tail -1 | jq .
```

### 场景 3：自动修复

```bash
# 1. 系统检测到 CPU 峰值（自动触发）
# → Reactor 匹配 Playbook
# → 自动降低心跳频率
# → 验证效果
# → 记录到 playbook_stats.json

# 2. 查看修复记录
cat aios/data/playbook_stats.json | jq '.[] | select(.name=="reduce_heartbeat_frequency")'
```

### 场景 4：自我改进

```bash
# 1. coder Agent 连续 3 次超时
# → Self-Improving Loop 触发
# → 分析原因（任务太复杂）
# → 自动增加 timeout 从 60s → 120s
# → 验证效果
# → 成功率提升

# 2. 查看改进报告
ls -lt aios/agent_system/data/reports/cycle_*.json | head -1 | xargs cat | jq .
```

---

## 快速开始

### 1. 创建一个分析任务

```bash
echo '{"type": "analysis", "message": "分析 AIOS 系统健康状况", "priority": "high"}' >> aios/agent_system/task_queue.jsonl
python aios/agent_system/auto_dispatcher.py heartbeat
```

### 2. 故意触发错误，观察 Reactor

```bash
# 创建一个会失败的任务
for i in {1..3}; do
  echo '{"type": "monitor", "message": "检查不存在的文件", "priority": "high"}' >> aios/agent_system/task_queue.jsonl
done

# 触发处理
python aios/agent_system/auto_dispatcher.py heartbeat

# 查看 Reactor 日志
tail -20 aios/reactor.log | jq .
```

### 3. 让同一个 Agent 重复失败，看 Self-Improving Loop

```bash
# 创建 5 个相同的失败任务
for i in {1..5}; do
  echo '{"type": "code", "message": "执行一个会超时的任务", "priority": "high"}' >> aios/agent_system/task_queue.jsonl
done

# 触发处理
python aios/agent_system/auto_dispatcher.py heartbeat

# 查看改进日志
tail -50 aios/agent_system/data/loop.log | jq 'select(.message | contains("improvement"))'
```

### 4. 查看 Evolution Engine 的进化报告

```bash
# 运行进化引擎（dry-run 模式）
python aios/agent_system/evolution_engine.py dry-run

# 查看最新报告
ls -lt aios/agent_system/data/evolution/reports/ | head -1 | xargs cat | jq .
```

---

## 常见问题

### Q1: 任务一直在队列里不处理？

**A:** 检查心跳是否正常运行：
```bash
# 查看心跳日志
tail -20 aios/heartbeat.log | jq .

# 手动触发心跳
python aios/agent_system/auto_dispatcher.py heartbeat
```

### Q2: Agent 一直失败怎么办？

**A:** 检查熔断器状态：
```bash
# 查看熔断器
python aios/agent_system/auto_dispatcher.py status

# 如果熔断了，等待 1 小时自动恢复，或手动重置
rm aios/agent_system/circuit_breaker_state.json
```

### Q3: Self-Improving Loop 没有触发？

**A:** 检查触发条件：
```bash
# 查看 Agent 统计
python aios/agent_system/auto_dispatcher.py status

# 确认失败次数是否达到阈值（高频 ≥3 次，低频 ≥2 次）
```

### Q4: 如何查看某个 Agent 的改进历史？

**A:**
```bash
# 查看改进报告
ls -lt aios/agent_system/data/reports/cycle_*.json | head -5

# 查看改进日志
tail -100 aios/agent_system/data/loop.log | jq 'select(.agent_id=="coder-dispatcher")'
```

---

## 下一步

1. **试试创建任务** - 从简单的分析任务开始
2. **观察自动修复** - 故意触发错误，看 Reactor 如何处理
3. **体验自我改进** - 让同一个 Agent 重复失败，观察改进循环
4. **查看进化报告** - 运行 Evolution Engine，看系统如何进化

**核心理念：** AIOS 不只是监控问题，而是自动解决问题、从失败中学习、持续进化。
