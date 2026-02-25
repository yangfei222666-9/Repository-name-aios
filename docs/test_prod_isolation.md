# Test/Prod 环境隔离 - 实施记录

**日期：** 2026-02-24  
**目标：** 把测试噪声从生产数据中隔离出来

## 改动清单

### 1. 配置文件
- ✅ `agent_configs.json` - 给每个 Agent 加 `env` 标签（prod/test）
- ✅ `env_config.json` - 新增环境过滤配置

### 2. 核心代码
- ✅ `agent_tracer.py` - `start_task()` 自动推断 env，`get_failure_patterns()` 支持 env 过滤
- ✅ `evolution_engine.py` - `_phase_observe()` 默认只分析 prod 环境
- ✅ `generate_alerts.py` - 事件生成时带 env 标签

### 3. 历史数据
- ✅ `patch_trace_env.py` - 给 100 条历史 trace 打补丁

## 效果验证

**隔离前：**
- 全部失败模式：4 个
- prod 失败模式：4 个（被 test 污染）
- test 失败模式：0 个

**隔离后：**
- 全部失败模式：4 个
- prod 失败模式：1 个（✅ 只剩真实问题：coder_001 Timeout）
- test 失败模式：3 个（✅ 噪声全部隔离）

## 立竿见影的收益

1. **进化引擎不再被测试数据污染**
   - division by zero × 42 次（test Agent）→ 不再影响 prod 分析
   - 模拟错误 × 6 次（test-001）→ 不再影响 prod 分析

2. **告警系统更清晰**
   - 4 条 OPEN 测试告警 → 可以单独查看或隐藏

3. **Dashboard 视图更准确**
   - 默认只看 prod，可选显示 test

## 下一步（未完成）

### 代码集成（需要时再做）
1. `core/event_bus.py` - publish() 自动从 agent_registry 读 env
2. `dashboard/server.py` - 加 `?env=prod|test|all` 参数
3. `alert_fsm.py` - 创建告警时带 env 标签（如果有这个文件）

### 测试覆盖
- 单元测试：env 过滤逻辑
- 集成测试：Dashboard 环境切换

## 关键设计

**自动推断规则：**
```python
env = "test" if "test" in agent_id.lower() else "prod"
```

**过滤接口：**
```python
analyzer.get_failure_patterns(min_occurrences=3, env="prod")  # 默认 prod
analyzer.get_failure_patterns(min_occurrences=3, env="all")   # 查看全部
```

**配置驱动：**
```json
{
  "default_view": "prod",
  "filter_rules": {
    "evolution": {
      "analyze_env": "prod",
      "exclude_test_failures": true
    }
  }
}
```

## 总结

✅ **核心目标达成：** 把训练靶场从生产机场隔离出来  
✅ **零破坏性：** 向后兼容，历史数据自动打补丁  
✅ **低成本：** 只改了 4 个文件，写了 1 个补丁脚本  
✅ **高收益：** prod 失败模式从 4 个降到 1 个（75% 噪声消除）

---

*"Separate test from production."*
