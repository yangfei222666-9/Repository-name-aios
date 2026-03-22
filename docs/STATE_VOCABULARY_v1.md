# 太极OS 状态词表 v1.0

**状态：** draft  
**创建时间：** 2026-03-11  
**最后更新：** 2026-03-11  
**维护者：** 小九 + 珊瑚海

---

## 一、设计原则

### 1. 一个字段只表达一个维度
不允许一个 `status` 字段同时表达"是否注册"、"是否可执行"、"最近运行结果"、"当前健康度"。

### 2. 生命周期、运行结果、健康度分开
- **生命周期状态** - 从注册到生产就绪的演进过程
- **运行结果状态** - 最近一次执行的结果
- **健康度状态** - 当前系统对该对象的健康判断

这三类状态不能混写。

### 3. 先覆盖 4 类对象，再谈迁移
词表必须能自然表达：
- Agent
- Skill
- Task
- Lesson

不能只围着 Agent 转。

---

## 二、4 类对象的最小状态模型

### 1. Agent / Skill 共用 3 层状态

#### A. readiness_status
**回答：** 准备到哪一步了？

**可选值：**
- `registered` - 已注册，但未验证可执行性
- `executable` - 已确认有可执行入口
- `validated` - 已通过治理验收
- `production-candidate` - 候选进入生产
- `production-ready` - 生产就绪
- `stable` - 长期稳定运行
- `not-executable` - 已注册但无可执行入口
- `not-evaluable` - 当前不可评估（缺少必要条件）
- `archived` - 已归档

#### B. run_status
**回答：** 最近一次运行结果是什么？

**可选值：**
- `no-sample` - 从未运行过
- `queued` - 已进入队列，等待执行
- `running` - 正在执行
- `success` - 执行成功
- `partial` - 部分成功
- `failed` - 执行失败
- `timeout` - 执行超时
- `blocked` - 被阻塞
- `canceled` - 被取消
- `zombie-recovered` - 僵尸任务已回收

#### C. health_status
**回答：** 当前健康度如何？

**可选值：**
- `healthy` - 健康
- `degraded` - 降级
- `blocked` - 阻塞
- `unknown` - 未知

#### 辅助标记
不是主状态，只保留布尔含义：
- `enabled: true/false` - 是否启用
- `routable: true/false` - 是否可路由

---

### 2. Task

Task 不需要 `readiness_status`（任务不存在"准备就绪"的概念），只需要：

#### A. run_status
**可选值：**（同 Agent/Skill 的 run_status）
- `queued`
- `running`
- `success`
- `partial`
- `failed`
- `timeout`
- `blocked`
- `canceled`
- `zombie-recovered`

#### B. health_status
**可选值：**（同 Agent/Skill 的 health_status）
- `healthy`
- `degraded`
- `blocked`
- `unknown`

---

### 3. Lesson

Lesson 不适合硬套 Agent/Skill 的 `readiness_status`。

它更需要一个**提炼进度状态**。

#### derivation_status
**回答：** 这条 lesson 现在提炼到哪一步了？

**可选值：**
- `captured` - 已记录，但还没开始处理
- `pending` - 等待提炼
- `extracting` - 正在提炼
- `rule-candidate` - 已形成规则候选
- `rule-derived` - 已正式转成 rule
- `rejected` - 提炼后判定不值得沉淀
- `not-evaluable` - 证据不足，当前不可评估
- `archived` - 已归档

**为什么不用 `regeneration_status`？**

现在很多 lesson 根本不是在"重新生成"，而是在等"提炼"。

`derivation_status` 更准确地表达了"从失败事件中提炼经验"的过程。

---

## 三、为什么这套更稳

### 1. 解决了旧模型的冗余
旧模型里：
- `mode` 和 `lifecycle_state` 完全重复，可以淘汰一套

新模型里：
- 只保留 `readiness_status`，废弃 `mode` 和 `lifecycle_state`

### 2. 补上了最缺的两个维度
审查中发现的两个缺口：
- **验证状态** - 现在有 `readiness_status`
- **最近运行结果** - 现在有 `run_status`

### 3. 明确引入了两个关键值
这两个必须有：
- `no-sample` - 从未运行过
- `not-evaluable` - 当前不可评估

没有它们，系统就会继续把"没跑过"当"正常"，把"没法判断"当"待处理"。

### 4. 真正覆盖了 4 类对象
- Agent：能表达 ✅
- Skill：能表达 ✅
- Task：能表达 ✅
- Lesson：能表达 ✅

这比现在只围着 Agent 转要完整很多。

---

## 四、4 个真实对象过一遍

### 1. GitHub_Researcher（已通过治理验收的 Learning Agent）

```json
{
  "name": "GitHub_Researcher",
  "readiness_status": "production-ready",
  "run_status": "success",
  "health_status": "healthy",
  "enabled": true,
  "routable": true
}
```

**解读：**
- 已通过验收，生产就绪
- 最近一次执行成功
- 当前健康
- 已启用，可路由

---

### 2. heartbeat_alert_deduper（已验证但未试运行的 Skill 草案）

```json
{
  "name": "heartbeat_alert_deduper",
  "readiness_status": "validated",
  "run_status": "no-sample",
  "health_status": "unknown",
  "enabled": false,
  "routable": false
}
```

**解读：**
- 已通过验证，但还在 draft registry
- 从未运行过（no-sample）
- 健康度未知（因为没跑过）
- 未启用，不可路由

---

### 3. 一个 queued task

```json
{
  "id": "task-20260311-190900",
  "type": "analysis",
  "run_status": "queued",
  "health_status": "healthy"
}
```

**解读：**
- 已进入队列，等待执行
- 当前健康（队列正常）

---

### 4. 一条待提炼的 lesson

```json
{
  "lesson_id": "lesson-66ff2238",
  "source_task_id": "task-1772188610619-6e669983",
  "task_description": "优化 Memory Manager 缓存策略",
  "derivation_status": "pending"
}
```

**解读：**
- 已记录失败事件
- 等待提炼为可复用规则

---

## 五、旧字段怎么映射

### Agent 旧字段 → 新字段

| 旧字段 | 新字段 | 映射规则 |
|---|---|---|
| `enabled` | 保留 | 直接保留 |
| `routable` | 保留 | 直接保留 |
| `mode` | **废弃候选** | 迁移到 `readiness_status` |
| `lifecycle_state` | **废弃候选** | 迁移到 `readiness_status` |
| `production_ready` | `readiness_status` | `true` → `production-ready`, `false` → 根据验证情况判断 |
| `tasks_completed/failed` | 不再直接当状态 | 只作统计，不作状态判断 |

### Lesson 旧字段

| 旧字段 | 新字段 | 映射规则 |
|---|---|---|
| `regeneration_status` | `derivation_status` | `pending` → `pending` |

### Task 旧字段

| 旧字段 | 新字段 | 映射规则 |
|---|---|---|
| `status` | `run_status` | `completed` → `success`, `failed` → `failed` |

---

## 六、Phase 1 迁移建议

**先不要全局替换**，按这个顺序来：

### 第一步：落正式文档
- ✅ `docs/STATE_VOCABULARY_v1.md`（本文档）

### 第二步：先做样例映射
选择 6 个真实对象，手动映射到新词表：
- GitHub_Researcher
- Code_Reviewer
- Error_Analyzer
- heartbeat_alert_deduper
- 1 个 queued task
- 1 条 pending lesson

### 第三步：先接 1 个消费者
- 健康报告（`aios_health_check.py`）

### 第四步：确认稳定后，再接
- 日报
- Dashboard
- Agent 总览

---

## 七、一句话结论

**Agent/Skill 用 3 层状态，Task 用运行状态，Lesson 用提炼状态。**

这样才能真正解决"状态混叠、无样本误判、4 类对象不统一"这 3 个根问题。

---

## 八、下一步

1. 用 4 类真实对象过一遍样例（验证词表能自然表达）
2. 确认无别扭后，进入 Phase 1 迁移
3. 先接健康报告，验证消费者能正常读取新词表
4. 逐步扩展到其他消费者

---

**版本：** v1.0 draft  
**状态：** 待审查  
**审查通过后：** 进入 Phase 1 迁移
