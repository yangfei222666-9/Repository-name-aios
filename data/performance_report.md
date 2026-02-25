# AIOS 性能监控报告

生成时间：2026-02-24 02:29:08

## 1. 路由延迟统计

- 决策总数：20
- 平均延迟：0.05 ms
- P50 延迟：0.00 ms
- P95 延迟：1.00 ms
- P99 延迟：1.00 ms
- 异常数量（>10ms）：0

## 2. 决策质量分析

- 平均置信度：0.85
- 低置信度决策数（<0.5）：0

### Agent 使用频率

- coder: 6 次 (30.0%)
- debugger: 6 次 (30.0%)
- reviewer: 3 次 (15.0%)
- optimizer: 1 次 (5.0%)
- tester: 1 次 (5.0%)
- monitor: 1 次 (5.0%)
- analyst: 1 次 (5.0%)
- researcher: 1 次 (5.0%)

### Reason Code 频率

- opus_quota_exceeded: 13 次
- sticky_applied: 7 次
- high_complexity: 2 次
- high_risk_high: 2 次
- low_complexity: 1 次
- high_error_rate: 1 次
- task_type_refactor: 1 次
- max_retries_exceeded: 1 次
- performance_degraded: 1 次
- task_type_test: 1 次
- resource_constrained: 1 次
- task_type_analyze: 1 次
- task_type_research: 1 次

## 3. 资源使用情况

- CPU 使用率：11.0%
- 内存使用率：43.1%

### 文件大小

- router_decisions.jsonl: 13.63 KB (13955 bytes)
- router_sticky.json: 1.19 KB (1221 bytes)

## 4. 优化建议

- 系统运行正常，暂无优化建议
