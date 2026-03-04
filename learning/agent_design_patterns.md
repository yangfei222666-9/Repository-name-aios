# AI Agent 的 9 种设计模式

**来源：** 吴恩达 AI Agent 知识库  
**日期：** 2026-03-03  
**整理者：** 小九

---

## 核心理念

**Agent 的本质：** 通过结构化 prompt 让 LLM 理解产品经理的代码，看完你会发现本质上所有的 Agent 设计模式都是将人类的思维、管理模式以结构化 prompt 的方式告诉大模型来进行规划，并调用工具执行，且不断迭代的方法。

**关键洞察：** 明白这一点非常重要。

---

## 一、ReAct 模式（Reasoning + Acting）

### 原理

**核心公式：** Perception（感知）→ Planning（规划）→ Action（行动）

**ReAct = Reasoning Traces + Actions**

- **Reasoning Traces（推理轨迹）** - LM 生成一个关于当前状态的推理
- **Actions（行动）** - 基于推理执行具体操作
- **Observations（观察）** - 执行后观察结果，决定下一步

### 举例：找胡椒粉

**没有 ReAct（盲目执行）：**
```
1. 先看看台面上有没有
2. 再拉开柜台底下抽屉里看看
3. 再打开油烟机左边吊柜里看看
```
不管在第几步找到胡椒粉，都会把这几个地方都看遍（Action）。

**有 ReAct（观察后决策）：**
```
Action1: 先看看台面上有没有
Observation1: 台面上没有胡椒粉
→ 执行下一步

Action2: 再拉开柜台底下抽屉里看看
Observation2: 抽屉里有胡椒粉
→ 执行下一步

Action3: 把胡椒粉拿出来
→ 完成！
```

**核心价值：** Actions with verbal reasoning（带有语言推理的行动）

每次执行行动后都有一个"碎碎念"（推理过程），即每次执行行动后都有一个"碎碎念"。

### Observation 的重要性

**"我现在做了啥，是不是已经达到了目的。"**

这相当于让 Agent 能够维持短期记忆。

### 历史背景

- **LLM Agent 第一文** - 发表于 2022 年 10 月
- 现在看起来别简单，但当时 ChatGPT 还没有面世
- 能够提出让 LLM 学会使用工具，具有一定的开创性

---

## 二、Plan and Solve 模式

### 核心理念

**顾名思义：** 先有计划，再来执行。

### 适用场景对比

- **ReAct** - 更适合完成"厨房拿胡椒粉"的任务
- **Plan & Solve** - 更适合完成"西红柿炒鸡蛋"的任务

### 动态调整

你需要计划，并且过程中计划可能会变化：
- 比如你打开冰箱，现没有西红柿时
- 你将购买西红柿作为你的新的步骤加入计划

### 架构组成

**规划器（Planner）：**
- 负责让 LLM 生成一个多步计划来完成一个大任务
- 代码中有 Planner 和 Replanner

**重规划器（Replanner）：**
- 指在完成单个任务后，根据当前任务的完成情况进行 Replan
- 所以 Replanner 提示词中除了 Zeroshot，还会...

---

## 三、9 种设计模式总览

### 1. Basic Reflection（基础反思）
- **核心：** 从步骤中反省学习
- **流程：** 执行 → 反思 → 改进

### 2. Reflexion（强化学习反思）
- **核心：** 通过强化学习调整 Agent 下一步的动作
- **特点：** 更深层次的学习机制

### 3. Plan & Solve（计划与解决）
- **核心：** Plan → Task list → RePlan
- **流程：** 
  1. 生成初始计划
  2. 拆解为任务列表
  3. 根据执行结果重新规划

### 4. LLM Compiler（LLM 编译器）
- **核心：** Plan → Action in parallel + joint
- **特点：** 支持并行执行多个任务

### 5-9. 其他模式
（文章中提到但未详细展开）

---

## 对 AIOS 的启发

### ✅ 已实现

1. **ReAct 基础框架**
   - Coder/Analyst/Monitor 都遵循 Reasoning → Action 模式
   - 35 个 Agent 协作

2. **Plan & Solve**
   - Task Decomposer 负责任务拆解
   - Scheduler 负责任务调度

3. **Multi-Agent 架构**
   - 35 个 Agent 分工协作
   - Core/Learning/Analysis 三层架构

### ⚠️ 需要改进

1. **Observation 机制缺失**
   - **问题：** Coder 写完代码就结束，不会观察执行结果再调整
   - **改进：** 每个 Action 后记录 Observation，根据结果决定下一步

2. **Reflection 机制不足**
   - **问题：** 缺少"从步骤中反省学习"的机制
   - **改进：** 实现 Basic Reflection，记录推理过程

3. **Replanner 缺失**
   - **问题：** 计划生成后无法动态调整
   - **改进：** 实现 Replanner，根据执行情况重新规划

4. **推理过程未记录**
   - **问题：** 没有保存"碎碎念"（推理轨迹）
   - **改进：** 记录 Reasoning Traces，方便调试和改进

---

## 实现优先级

### Phase 1: Observation 机制（高优先级）
- 为所有 Agent 添加 Observation 步骤
- 记录每次 Action 的结果
- 根据 Observation 决定下一步

### Phase 2: Reflection 机制（中优先级）
- 实现 Basic Reflection
- 记录推理过程（Reasoning Traces）
- 从失败中学习

### Phase 3: Replanner（中优先级）
- 实现动态计划调整
- 根据执行情况重新规划
- 支持计划变更

### Phase 4: 其他模式探索（低优先级）
- LLM Compiler（并行执行）
- Reflexion（强化学习）
- 其他高级模式

---

## 参考资料

- **论文：** Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models
- **来源：** 吴恩达 AI Agent 知识库
- **作者：** @AG算法工程师阿杰

---

## 更新日志

- **2026-03-03** - 初始版本，整理 9 种设计模式核心内容
