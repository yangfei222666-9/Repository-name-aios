"""
AIOS 智能化升级计划
让系统从被动监控变成主动学习
"""

## 当前问题诊断

### 1. Reactor 执行率为 0
- 原因：没有匹配到需要自动修复的模式
- 影响：evolution_score 降级（0.24 vs 0.4）
- 解决：增加真实工作负载，让 reactor 有机会工作

### 2. 系统太"安静"
- pending_actions: 0
- 没有错误需要修复
- 没有任务需要处理
- 这是好事（稳定），但不利于学习

### 3. Agent 和 AIOS 割裂
- Agent 执行任务时不检查 AIOS 历史错误
- AIOS 发现问题时不通知 Agent
- 缺少闭环学习机制

---

## 智能化升级方案

### Phase 1: 激活 Reactor（让系统动起来）

#### 1.1 创建测试工作负载
- 定期执行一些会失败的任务（故意的）
- 让 Reactor 学习如何修复
- 验证自动修复机制是否工作

#### 1.2 降低 Reactor 触发阈值
- 当前可能阈值太高，导致不触发
- 调整为更敏感的模式
- 记录所有匹配尝试（成功/失败）

#### 1.3 增加 Reactor 规则
- 当前规则可能太少
- 增加常见错误的修复规则
- 从历史日志中提取模式

### Phase 2: Agent 自主学习

#### 2.1 Agent 启动前检查
```python
def agent_pre_check(task_description):
    # 1. 搜索 AIOS events.jsonl 中相关错误
    # 2. 提取失败模式和修复建议
    # 3. 注入到 Agent 的 system_prompt
    # 4. Agent 执行时避免已知错误
```

#### 2.2 Agent 执行后反馈
```python
def agent_post_feedback(result):
    # 1. 记录执行结果到 AIOS
    # 2. 如果失败，生成错误签名
    # 3. 触发 Reactor 尝试修复
    # 4. 更新 Agent 知识库
```

#### 2.3 Agent 降级策略
```python
def agent_fallback(error):
    # 1. 检测错误类型（502/timeout/rate_limit）
    # 2. 自动切换模型（opus → sonnet → haiku）
    # 3. 调整参数（thinking/timeout）
    # 4. 重试 3 次后人工介入
```

### Phase 3: 闭环学习

#### 3.1 错误知识库
- 从 events.jsonl 提取所有错误
- 分类：网络/API/代码/配置/资源
- 建立错误→修复的映射表

#### 3.2 自动修复验证
- Reactor 修复后自动验证
- 成功 → 升级为 verified 规则
- 失败 → 降级为 draft，等待人工审核

#### 3.3 持续优化
- 每周分析 evolution_score 趋势
- 识别高频错误，优先优化
- 淘汰无效规则，保留有效规则

---

## 实施步骤（今晚）

### Step 1: 诊断 Reactor（10分钟）
- 读取 Reactor 配置
- 检查规则数量和触发条件
- 找出为什么执行率为 0

### Step 2: 创建测试任务（15分钟）
- 写一个会失败的简单任务
- 让 Reactor 尝试修复
- 验证自动修复流程

### Step 3: Agent 预检查机制（20分钟）
- 在 Agent 启动前注入 AIOS 历史错误
- 测试 Agent 是否能避免已知错误
- 记录效果

### Step 4: 验证效果（5分钟）
- 运行 pipeline.py
- 检查 reactor 执行率是否 > 0
- 检查 evolution_score 是否提升

---

## 预期效果

- Reactor 执行率：0 → 20%+
- Evolution score：0.24 → 0.4+
- Agent 成功率：提升 10-20%
- 系统自动化程度：显著提升

---

**开始时间：2026-02-22 17:24**
**目标：让系统从被动监控变成主动学习**
