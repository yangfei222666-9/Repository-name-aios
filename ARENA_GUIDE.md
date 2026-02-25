# AIOS Agent Arena - 对抗系统使用指南

## 🥊 概述

AIOS Agent Arena 让 AIOS 和 Agent 互相挑战、对抗、学习，通过竞争来进化。

## 对抗模式

### 1. AIOS 攻击模式
AIOS 向 Agent 发起挑战，测试 Agent 的能力。

### 2. Agent 攻击模式
Agent 向 AIOS 发起挑战，测试 AIOS 的能力。

### 3. 协作模式
AIOS 和 Agent 一起解决问题。

### 4. 竞争模式
AIOS 和 Agent 比赛谁更快/更好。

---

## 挑战类型

### 性能挑战（Performance）
- 测试速度和吞吐量
- 例：10 秒内完成 100 个任务

### 可靠性挑战（Reliability）
- 测试稳定性和容错能力
- 例：502 错误下保持 95% 成功率

### 创造力挑战（Creativity）
- 测试创新和解决方案多样性
- 例：用 3 种不同方法解决问题

### 效率挑战（Efficiency）
- 测试资源利用率
- 例：用最少的 token 完成任务

### 问题解决挑战（Problem Solving）
- 测试综合能力
- 例：修复 5 个不同类型的错误

---

## 使用方法

### 1. AIOS 发起挑战

```python
from core.agent_arena import get_arena, ChallengeType

arena = get_arena()

# AIOS 挑战 Agent
challenge = arena.aios_challenge_agent(ChallengeType.PERFORMANCE)

print(f"挑战: {challenge['title']}")
print(f"任务: {challenge['task']}")
print(f"成功标准: {challenge['success_criteria']}")
```

### 2. Agent 发起挑战

```python
# Agent 挑战 AIOS
challenge = arena.agent_challenge_aios(ChallengeType.RELIABILITY)

print(f"挑战: {challenge['title']}")
```

### 3. 协作挑战

```python
# AIOS 和 Agent 一起解决问题
challenge = arena.collaborative_challenge()

print(f"AIOS 角色: {challenge['aios_role']}")
print(f"Agent 角色: {challenge['agent_role']}")
```

### 4. 竞争挑战

```python
# AIOS 和 Agent 比赛
challenge = arena.competitive_challenge()

print(f"任务: {challenge['task']}")
```

### 5. 记录战斗结果

```python
# 记录结果（用户作为裁判）
arena.record_battle(
    challenge_id=challenge["id"],
    winner="agent",  # aios/agent/draw
    aios_score=85,
    agent_score=95,
    details={"reason": "Agent 更快完成"}
)
```

### 6. 查看排行榜

```python
# 生成报告
report = arena.generate_arena_report()
print(report)
```

---

## 集成到心跳

在 `HEARTBEAT.md` 中添加每日对抗：

```markdown
### 每天：AIOS vs Agent 对抗
- 随机选择一个挑战类型
- AIOS 和 Agent 轮流发起挑战
- 记录结果到排行榜
- 每周生成对抗报告
```

---

## 对抗流程

```
1. 发起挑战
   ↓
2. 执行任务
   ↓
3. 评估结果
   ↓
4. 用户裁判
   ↓
5. 记录排行榜
   ↓
6. 双方学习
```

---

## 示例场景

### 场景 1：性能对决

**AIOS 挑战：** "Agent，你能在 10 秒内创建 100 个 Agent 吗？"

**Agent 响应：** 
- 使用 Failover 机制
- 并发创建
- 9.5 秒完成

**结果：** Agent 获胜（95 分 vs 85 分）

---

### 场景 2：可靠性测试

**Agent 挑战：** "AIOS，我会让 CPU 飙到 90%，你能保持运行吗？"

**AIOS 响应：**
- 启动资源监控
- 降低并发数
- 触发 Reactor 自动修复

**结果：** AIOS 获胜（90 分 vs 80 分）

---

### 场景 3：协作任务

**挑战：** "一起将系统性能提升 50%"

**AIOS：** 优化调度算法，减少队列堆积  
**Agent：** 优化执行效率，减少重试次数

**结果：** 平局（双方都得 95 分）

---

## 学习机制

### AIOS 学习

从 Agent 的成功策略中学习：
- Agent 如何处理 502 错误？
- Agent 如何优化资源使用？
- Agent 的创新解决方案是什么？

### Agent 学习

从 AIOS 的调度策略中学习：
- AIOS 如何优先级排序？
- AIOS 如何并发处理？
- AIOS 的自动修复规则是什么？

---

## 排行榜

```
============================================================
🥊 AIOS Agent Arena 排行榜
============================================================

🤖 AIOS:
  胜: 15, 负: 12, 平: 3
  平均得分: 88.50

👤 Agent:
  胜: 12, 负: 15, 平: 3
  平均得分: 85.20

🏆 当前领先: AIOS (+3)

============================================================
```

---

## 进化路径

### 短期（1-2 周）
- 发现各自的优势和劣势
- 学习对方的策略
- 优化自己的算法

### 中期（1-3 个月）
- 形成互补的能力
- 协作效率提升
- 竞争水平提高

### 长期（3-12 个月）
- 双方都进化到更高水平
- 形成自我进化的闭环
- 系统整体性能大幅提升

---

## 用户角色

你作为裁判，决定：
- 谁赢了这场对抗
- 得分是多少
- 哪些策略值得学习

你的判断会影响：
- 排行榜
- 学习方向
- 进化路径

---

**让 AIOS 和 Agent 在对抗中成长！** 🥊💪
