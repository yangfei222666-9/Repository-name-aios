# AIOS Full Cycle Demo - 10 秒快速开始

## 🚀 一键运行

```bash
cd C:\Users\A\.openclaw\workspace\aios
python demo_full_cycle.py
```

**预期输出：**
- ✅ 场景 1: Reactor 自动修复（FileNotFoundError）
- ✅ 场景 2: Self-Improving Loop（超时改进）
- ✅ 场景 3: Evolution Engine（Prompt 进化）
- 📊 完整的可观测数据（Traces + Metrics + Logs）

**总耗时：** ~30 秒

---

## 📁 输出文件

### 1. Traces（分布式追踪）
**位置：** `aios/observability/traces/`

**内容：** 每个场景的完整执行轨迹
```json
{
  "trace_id": "abc123def456",
  "service": "AIOS-Demo",
  "spans": [
    {
      "span_id": "span-001",
      "name": "scenario-1-reactor",
      "duration_ms": 2500,
      "status": "success"
    }
  ]
}
```

### 2. Metrics（实时指标）
**位置：** `aios/observability/metrics/`

**内容：** 所有场景的指标汇总
```json
{
  "counters": {
    "tasks.created": 9,
    "tasks.failed": 3,
    "reactor.fixes": 1,
    "improvements.applied": 1
  },
  "gauges": {
    "reactor.success_rate": 1.0,
    "agent.success_rate{agent=coder}": 1.0
  },
  "histograms": {
    "task.duration_sec": {
      "count": 3,
      "avg": 65.0,
      "p95": 65.0
    }
  }
}
```

### 3. Logs（结构化日志）
**位置：** `aios/observability/logs/`

**内容：** 所有操作的详细日志
```json
{
  "timestamp": "2026-02-25T16:05:12.345678",
  "trace_id": "abc123def456",
  "span_id": "span-001",
  "level": "INFO",
  "service": "Reactor",
  "message": "Reactor 检测到 3 个失败事件",
  "task_id": "monitor-1",
  "error": "FileNotFoundError"
}
```

---

## 🎯 3 个场景详解

### 场景 1: Reactor 自动修复

**问题：** 3 个监控任务因 `FileNotFoundError` 失败

**修复流程：**
1. 检测到 3 个失败事件
2. 匹配 Playbook: `pb-021-file-not-found-fix`
3. 执行修复：创建缺失路径
4. 验证成功：路径已存在

**关键指标：**
- 失败任务: 3
- 修复次数: 1
- 成功率: 100%
- 修复时间: ~500ms

### 场景 2: Self-Improving Loop

**问题：** coder Agent 连续 3 次超时失败

**改进流程：**
1. 检测到失败 3/3 次（触发条件）
2. 分析根因：timeout 60s 不足
3. 生成建议：增加 timeout → 120s
4. 自动应用（低风险）
5. 验证效果：成功率 0% → 100%

**关键指标：**
- 失败任务: 3
- 改进建议: 1
- 改进应用: 1
- 成功率提升: 0% → 100%

### 场景 3: Evolution Engine

**问题：** Prompt 缺少错误处理和超时预警

**进化流程：**
1. 收集 15 条追踪数据
2. 分析发现 2 个 Prompt 缺口
3. 生成 2 个 Prompt 补丁
4. 应用到 coder Agent
5. 知识传播到 3 个低成功率 Agent

**关键指标：**
- Prompt 缺口: 2
- 补丁生成: 2
- 进化应用: 1
- 知识传播: 3

---

## 📊 可观测性验证

### 查看 Traces
```bash
# 查看最新的 Trace
ls -lt aios/observability/traces/ | head -1
cat aios/observability/traces/trace_*.json | jq .
```

### 查看 Metrics
```bash
# 查看最新的 Metrics
ls -lt aios/observability/metrics/ | head -1
cat aios/observability/metrics/metrics_*.json | jq .
```

### 查看 Logs
```bash
# 查看最新的 10 条日志
tail -10 aios/observability/logs/*.log | jq .
```

---

## 🔧 自定义运行

### 只运行特定场景
```python
# 编辑 demo_full_cycle.py，注释掉不需要的场景
# scenario_1_reactor_fix()
scenario_2_self_improving()
# scenario_3_evolution()
```

### 调整日志级别
```python
logger = get_logger("Demo", min_level="debug")  # 显示所有日志
```

### 导出 Prometheus 格式
```python
metrics.export(format="prometheus")  # 未来支持
```

---

## ✅ 验收标准

运行成功后，你应该看到：

1. **3 个场景全部成功** ✓
2. **Traces 文件已生成** ✓
3. **Metrics 文件已生成** ✓
4. **Logs 文件已生成** ✓
5. **总耗时 < 60 秒** ✓

---

## 🚀 下一步

1. **集成到 CI/CD** - 作为回归测试
2. **Dashboard 可视化** - 实时监控
3. **告警规则** - 自动通知
4. **性能基准** - 持续优化

---

**核心价值：** 30 秒内完整验证 AIOS 的 3 大核心能力（自动修复、自我改进、自主进化），全程可观测、可追踪、可复现。
