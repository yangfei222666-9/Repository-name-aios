# AIOS 每日优化报告

生成时间：2026-02-24 02:35 (CST)

---

## 一、系统健康概览

| 指标 | 值 | 状态 |
|------|-----|------|
| 进化分数 | 0.4572 | ✅ healthy |
| 平均路由置信度 | 0.816 | ✅ 正常 |
| 路由延迟 P95 | 1.00 ms | ✅ 极低 |
| CPU 使用率 | 11.0% | ✅ 正常 |
| 内存使用率 | 43.1% | ✅ 正常 |
| 熔断器状态 | 3 open / 1 closed | ⚠️ 需关注 |
| Playbook 成功率 | 100% (全部14个) | ✅ 优秀 |
| 数据目录大小 | 340.7 KB | ✅ 正常 |

## 二、发现的问题

### P0 - 无

### P1 - 需关注

#### 1. opus_quota_exceeded 占比过高 (13/46 = 28%)
- 路由决策中 `opus_quota_exceeded` 是最频繁的 reason_code
- 说明 Opus 配额经常触顶，导致降级到 Sonnet
- 影响：高复杂度任务（refactor/deploy）可能因降级而质量下降
- 建议：评估是否需要提升 Opus 配额，或优化 Opus 使用策略

#### 2. sticky_applied 过度使用 (9/46 = 20%)
- Sticky 路由占比较高，可能导致路由僵化
- 所有 10 个任务类型都有 sticky 绑定，且全部在同一时间段创建
- 建议：考虑缩短 sticky TTL 或增加 sticky 失效条件

#### 3. 熔断器长期 open
- `resource.memory_high:memory_handler` 已 open 超过 2 小时
- `event2:playbook2` 同样长期 open
- `CPU 峰值处理` 和 `Agent 错误处理` 也处于 open 状态
- 建议：检查这些熔断器是否需要手动 reset 或自动恢复机制

### P2 - 低优先级

#### 4. feedback_suggestions.jsonl 重复膨胀（已修复）
- 324 行中大量重复建议（同一 playbook 的相同建议反复记录）
- 已自动去重至 13 行，节省 63.8 KB (96% 压缩)

#### 5. 进化分数增长缓慢
- 从 0.30 (degraded) 恢复到 0.4572 (healthy)
- auto_close_rate 仅 0.25，false_positive_rate 已降至 2.3%
- reactor_score 0.543，仍有提升空间
- 建议：提高 auto_close_rate 可显著提升进化分数

#### 6. __pycache__ 占用空间（已清理）
- 451 KB 的 .pyc 缓存文件已清理

## 三、已自动应用的优化

| # | 优化项 | 风险 | 效果 |
|---|--------|------|------|
| 1 | 去重 feedback_suggestions.jsonl | 低 | 324→13 行，节省 63.8 KB |
| 2 | 清理 __pycache__ | 低 | 释放 451 KB |

## 四、需要人工确认的高风险优化

### 🔴 1. 重置长期 open 的熔断器
- 涉及：memory_handler, event2:playbook2, CPU峰值处理, Agent错误处理
- 风险：如果底层问题未解决，重置后可能立即再次触发
- 建议操作：先检查各熔断器对应的根因是否已消除，再手动 reset

### 🟡 2. 调整 Opus 配额策略
- 当前 12 次 Opus 调用集中在同一秒（疑似测试数据）
- 建议：清理 router_budget.json 中的测试数据，重新评估真实 Opus 使用量
- 或考虑在 router_config.json 中调整 complexity_rules，减少不必要的 Opus 调用

### 🟡 3. 优化 Sticky 路由策略
- 当前所有 10 个任务类型都有 sticky 绑定
- 建议：为低复杂度任务（coding, test, monitor）移除 sticky，让路由器动态选择
- 预期收益：提高路由灵活性，减少 sticky_applied 占比

## 五、数据文件大小监控

| 文件 | 大小 | 趋势 |
|------|------|------|
| pipeline_runs.jsonl | 73.6 KB | ⚠️ 最大，建议定期归档 |
| events.jsonl | 65.9 KB | ⚠️ 较大 |
| reactions.jsonl | 60.3 KB | ⚠️ 较大 |
| decisions.jsonl | 44.8 KB | 正常 |
| verify_log.jsonl | 28.2 KB | 正常 |
| evolution_history.jsonl | 23.7 KB | 正常 |
| router_decisions.jsonl | 17.3 KB | 正常 |
| feedback_suggestions.jsonl | 2.7 KB | ✅ 已优化 |

建议：当单个 JSONL 文件超过 100 KB 时自动归档旧数据。

## 六、下次优化重点

1. 监控 pipeline_runs.jsonl / events.jsonl / reactions.jsonl 增长速度
2. 跟踪 Opus 配额使用的真实模式（排除测试数据干扰）
3. 评估熔断器自动恢复机制的可行性
4. 关注进化分数是否持续上升

---
*报告由 AIOS 持续优化专员自动生成*
