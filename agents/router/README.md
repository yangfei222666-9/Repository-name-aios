# Fast/Slow Thinking Router

**版本：** v1.0  
**作者：** Grok + 小九  
**日期：** 2026-03-05

## 核心功能

根据任务复杂度、Evolution Score、当前卦象智能路由模型：
- **Fast 模型：** Claude Sonnet 4.6（简单任务，成本低）
- **Slow 模型：** Claude Opus 4.6 / o1（复杂任务，质量高）

## 集成状态

✅ **已集成：**
- `agents/router/agent_router.py` - 核心路由逻辑
- `agent_system/real_coder.py` - Coder Agent 集成
- `tests/test_agent_router.py` - 单元测试（3/3 通过）

## 使用方式

### 1. 直接调用

```python
from agents.router.agent_router import route_task, TaskIndicators

indicators: TaskIndicators = {
    "needs_code": True,
    "high_risk": True,
    "est_lines": 180,
    "dependencies": 5,
    "requires_reasoning": True
}

model = route_task(
    task_id="task-001",
    task_description="实现 LowSuccess_Agent Phase 3 重生逻辑",
    indicators=indicators
)

# model = "slow" (Opus 4.6) 或 "fast" (Sonnet 4.6)
```

### 2. 集成到 Agent

参考 `real_coder.py` 的集成方式：

```python
from agents.router.agent_router import route_task, TaskIndicators

def call_claude_api(prompt: str, model: str = None, task_description: str = None):
    if model is None and task_description:
        # 分析任务指标
        indicators: TaskIndicators = {
            "needs_code": True,
            "high_risk": "修复" in task_description or "critical" in task_description.lower(),
            "est_lines": len(task_description.split()) * 3,
            "dependencies": task_description.count("import"),
            "requires_reasoning": "算法" in task_description or "优化" in task_description,
            "task_description": task_description
        }
        
        # 路由决策
        model_choice = route_task(
            task_id=f"coder-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            task_description=task_description,
            indicators=indicators
        )
        
        # 映射到实际模型名称
        model = "claude-opus-4-6" if model_choice == "slow" else "claude-sonnet-4-6"
    
    # 调用 API...
```

## 路由逻辑

### 1. 基础复杂度计算（0-1.0）

- **文字量：** `min(words / 150, 0.4)`
- **代码量：** 如果 `needs_code=True` 且 `est_lines > 50` → +0.35
- **高风险：** 如果 `high_risk=True` → +0.4
- **依赖数：** 如果 `dependencies > 3` → +0.2
- **需要推理：** 如果 `requires_reasoning=True` → +0.3

### 2. Evolution Score 强干预

- 如果 `evolution_score < 0.90` → +0.25（强制慢模型）

### 3. 坤卦特殊加成

- 如果当前卦象 = "坤卦" → +0.10（厚德载物，更稳健）

### 4. 最终决策

- `complexity > 0.65` → **slow**（Opus 4.6）
- `complexity ≤ 0.65` → **fast**（Sonnet 4.6）

## 测试结果

```bash
cd C:\Users\A\.openclaw\workspace\aios
python -m pytest tests/test_agent_router.py -v
```

**输出：**
```
tests/test_agent_router.py::TestRouter::test_kun_gua_slow PASSED         [ 33%]
tests/test_agent_router.py::TestRouter::test_medium_complexity PASSED    [ 66%]
tests/test_agent_router.py::TestRouter::test_simple_fast PASSED          [100%]

============================== 3 passed in 0.03s
```

## 验证案例

### 简单任务 → Fast

```bash
python real_coder.py "写一个简单的 hello world 函数"
```

**输出：**
```
🚦 Router 决策: fast → claude-sonnet-4-6
[OK] 代码生成完成 (119 字符)
[OK] 执行成功
```

### 复杂任务 → Slow

```bash
python real_coder.py "实现一个复杂的算法：快速排序，并优化性能"
```

**预期输出：**
```
🚦 Router 决策: slow → claude-opus-4-6
[OK] 代码生成完成 (XXX 字符)
[OK] 执行成功
```

## 预期效果

**24 小时观察期（2026-03-05 ~ 2026-03-06）：**

1. **成功率提升：** coder-dispatcher 从 75% → 88%+
2. **成本下降：** 日成本 ↓35-40%（简单任务用 Sonnet）
3. **质量保证：** 复杂任务用 Opus，质量不降
4. **坤卦加成：** 稳定期自动触发 +0.10 加成

## 监控指标

**集成到 Heartbeat v5.0：**
- Router 决策日志（`router_decisions.jsonl`）
- 模型使用统计（fast/slow 比例）
- 成功率变化（按模型分组）
- 成本变化（按模型分组）

**集成到每日简报：**
- Router 决策统计
- 模型使用分布
- 成功率对比（fast vs slow）
- 成本节省统计

## 下一步

1. ✅ **集成到 real_coder.py**（已完成）
2. ⏳ **24 小时观察期**（2026-03-05 12:00 ~ 2026-03-06 12:00）
3. ⏳ **集成到 Heartbeat**（自动监控）
4. ⏳ **集成到每日简报**（统计报告）
5. ⏳ **集成到 Dashboard**（可视化）

## 维护者

- **Grok**（设计 + 指导）
- **小九**（实现 + 集成）
- **珊瑚海**（需求 + 验证）

---

**最后更新：** 2026-03-05 12:15  
**状态：** ✅ 生产就绪，进入观察期
