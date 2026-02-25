# AIOS 自学习工作流

## 概述

AIOS 自学习工作流让系统能从每次执行中学习和改进，持续优化性能。

## 学习内容

### 1. Provider 性能学习
- **学什么：** 哪个模型（Sonnet/Opus/Haiku）成功率高、速度快
- **怎么用：** 自动选择最佳模型
- **数据：** `aios/learning/provider_stats.json`

### 2. Playbook 效果学习
- **学什么：** 哪些自动修复规则有效、哪些无效
- **怎么用：** 建议禁用低效规则
- **数据：** `aios/learning/playbook_stats.json`

### 3. 任务路由学习
- **学什么：** 哪种任务适合哪个 Agent 模板
- **怎么用：** 自动选择最佳 Agent
- **数据：** `aios/learning/task_routing.json`

### 4. 资源阈值学习
- **学什么：** CPU/内存告警阈值是否合理
- **怎么用：** 建议调整阈值，减少误报
- **数据：** `aios/learning/threshold_history.jsonl`

### 5. 用户反馈学习
- **学什么：** 用户对自动化动作的反馈
- **怎么用：** 改进决策逻辑
- **数据：** `aios/learning/user_feedback.jsonl`

---

## 使用方法

### 1. 记录执行结果

在代码中集成学习记录：

```python
from core.learning_workflow import get_learning_workflow

workflow = get_learning_workflow()

# 记录 Provider 执行
workflow.record_provider_execution(
    provider="claude-haiku-4-5",
    success=True,
    duration=2.5,
    task_type="agent_spawn"
)

# 记录 Playbook 执行
workflow.record_playbook_execution(
    playbook_id="pb-001-network-retry",
    success=True,
    duration=0.5,
    event_type="agent.error"
)

# 记录任务路由
workflow.record_task_routing(
    task_type="code",
    agent_template="coder",
    success=True,
    duration=45.0
)
```

### 2. 查询学习结果

```python
# 获取最佳 Provider
best_provider = workflow.get_best_provider(task_type="agent_spawn")
print(f"最佳 Provider: {best_provider}")

# 获取 Playbook 推荐
recommendations = workflow.get_playbook_recommendations()
for rec in recommendations:
    print(f"{rec['playbook_id']}: {rec['action']} - {rec['reason']}")

# 获取最佳 Agent 模板
best_agent = workflow.get_best_agent_template(task_type="code")
print(f"最佳 Agent: {best_agent}")
```

### 3. 生成学习报告

```python
# 生成报告
report = workflow.generate_learning_report()
print(report)
```

或者运行心跳任务：

```bash
python -X utf8 aios/learning_heartbeat.py
```

---

## 集成点

### 1. Provider Manager 集成

在 `provider_manager.py` 中记录执行结果：

```python
def execute_with_failover(...):
    # ... 执行逻辑 ...
    
    # 记录结果
    workflow = get_learning_workflow()
    workflow.record_provider_execution(
        provider=provider_name,
        success=result["success"],
        duration=duration,
        task_type=task_type
    )
```

### 2. Reactor 集成

在 `production_reactor.py` 中记录执行结果：

```python
def execute(self, playbook, event):
    # ... 执行逻辑 ...
    
    # 记录结果
    workflow = get_learning_workflow()
    workflow.record_playbook_execution(
        playbook_id=playbook["id"],
        success=result["success"],
        duration=duration,
        event_type=event["type"]
    )
```

### 3. Auto Dispatcher 集成

在 `auto_dispatcher.py` 中记录路由结果：

```python
def _dispatch_task(self, task):
    # ... 分发逻辑 ...
    
    # 记录结果
    workflow = get_learning_workflow()
    workflow.record_task_routing(
        task_type=task_type,
        agent_template=template["label"],
        success=result["status"] == "pending",
        duration=duration
    )
```

---

## 学习报告示例

```
============================================================
AIOS 自学习报告
============================================================

📊 Provider 性能:
  claude-haiku-4-5: 成功率 95.0%, 平均时长 2.30s, 执行 20 次
  claude-sonnet-4-6: 成功率 75.0%, 平均时长 3.50s, 执行 12 次
  claude-opus-4-6: 成功率 70.0%, 平均时长 5.20s, 执行 10 次

💡 Playbook 推荐:
  pb-003-process-restart: disable - Low success rate: 25.0%
  pb-001-network-retry: keep_enabled - High success rate: 90.0%

🎯 任务路由学习:
  code → coder (成功率 85.0%)
  analysis → analyst (成功率 90.0%)
  monitor → monitor (成功率 95.0%)

============================================================
```

---

## 自动化

在 `HEARTBEAT.md` 中已添加每日学习任务：

```markdown
### 每天：AIOS 自学习分析
- 运行学习心跳
- 生成学习报告
- 如果发现优化建议，主动提醒
```

---

## 下一步

1. **集成到现有组件** - 在 Provider Manager、Reactor、Auto Dispatcher 中添加学习记录
2. **用户反馈收集** - 添加反馈接口，让用户可以评价自动化动作
3. **自动应用学习结果** - 根据学习结果自动调整配置（需要人工确认）

---

## 注意事项

1. **数据积累** - 需要至少 10-20 次执行才能得出有意义的结论
2. **定期清理** - 学习数据会持续增长，建议定期归档旧数据
3. **人工审核** - 学习建议需要人工审核后再应用，避免误判

---

**让 AIOS 越用越聪明！** 🧠
