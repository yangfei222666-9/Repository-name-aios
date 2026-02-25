# 反馈闭环系统设计文档

## 目标
建立一个简单有效的反馈机制，让小九能从珊瑚海的反馈中学习，逐步优化行为。

## 核心原则
1. **低摩擦** — 反馈要简单，不打断正常对话
2. **可追溯** — 每条反馈都能关联到具体的行为
3. **可量化** — 能够统计和分析
4. **自动应用** — 学到的经验自动影响未来决策

## 反馈类型

### 1. 显式反馈（用户主动给）
- **有用** / **没用** — 最简单的二元反馈
- **很好** / **一般** / **不好** — 三级评分
- **具体意见** — 文字描述

### 2. 隐式反馈（系统自动推断）
- 用户采纳了建议 → 正反馈
- 用户忽略了建议 → 负反馈
- 用户纠正了我的错误 → 强负反馈
- 用户重复问同样的问题 → 上次回答不够好

## 数据格式

### feedback.jsonl（反馈记录）
```json
{
  "timestamp": 1708668000,
  "feedback_id": "fb-20260223-001",
  "type": "explicit",
  "value": "useful",
  "context": {
    "action_type": "suggestion",
    "action_id": "suggest-open-music",
    "message": "通常这个时间你会听音乐，要不要打开 QQ音乐？",
    "category": "habit_suggestion"
  },
  "user_comment": null
}
```

### feedback_stats.json（统计汇总）
```json
{
  "last_updated": "2026-02-23T15:04:00",
  "by_category": {
    "habit_suggestion": {
      "total": 10,
      "useful": 7,
      "not_useful": 3,
      "acceptance_rate": 0.7
    },
    "health_reminder": {
      "total": 5,
      "useful": 4,
      "not_useful": 1,
      "acceptance_rate": 0.8
    }
  },
  "by_action_type": {
    "suggestion": {"useful": 11, "not_useful": 4},
    "reminder": {"useful": 8, "not_useful": 2},
    "alert": {"useful": 5, "not_useful": 1}
  },
  "recent_trends": {
    "last_7_days": {
      "total": 15,
      "acceptance_rate": 0.73
    }
  }
}
```

### learned_rules.json（学到的规则）
```json
{
  "rules": [
    {
      "rule_id": "lr-001",
      "description": "珊瑚海不喜欢工作时间被打断玩游戏的建议",
      "condition": {
        "time_range": ["09:00", "18:00"],
        "weekday": [0, 1, 2, 3, 4],
        "action_type": "gaming_suggestion"
      },
      "action": "suppress",
      "confidence": 0.85,
      "evidence_count": 6,
      "created_at": "2026-02-25T10:30:00"
    },
    {
      "rule_id": "lr-002",
      "description": "珊瑚海喜欢编程时听音乐的建议",
      "condition": {
        "activity": "coding",
        "action_type": "music_suggestion"
      },
      "action": "boost",
      "confidence": 0.9,
      "evidence_count": 8,
      "created_at": "2026-02-26T14:20:00"
    }
  ]
}
```

## 反馈触发方式

### 方式 1：关键词识别（最简单）
用户说：
- "有用" / "好" / "不错" / "👍" → 正反馈
- "没用" / "不好" / "别这样" / "👎" → 负反馈
- "很好" / "完美" / "太棒了" → 强正反馈

### 方式 2：显式命令
```
/feedback useful [comment]
/feedback not_useful [comment]
/feedback rate 5
```

### 方式 3：隐式推断
- 我建议"打开 QQ音乐"，5 分钟内检测到 QQ音乐启动 → 正反馈
- 我提醒"游戏时间过长"，但继续玩了 2 小时 → 负反馈
- 我说"要不要提交 Git"，1 分钟内检测到 git commit → 正反馈

## 学习机制

### 规则提取（每周运行一次）
1. 统计各类建议的接受率
2. 识别模式：
   - 什么时间/场景下的建议更容易被接受
   - 什么类型的建议经常被拒绝
3. 生成规则：
   - 接受率 > 80% → boost（增加建议频率）
   - 接受率 < 30% → suppress（减少建议频率）
   - 接受率 < 10% → block（完全停止该类建议）

### 规则应用
在生成建议前，检查 learned_rules.json：
- 如果命中 suppress 规则 → 降低优先级
- 如果命中 boost 规则 → 提高优先级
- 如果命中 block 规则 → 不生成建议

### 置信度衰减
- 规则的置信度会随时间衰减（每月 -5%）
- 如果新证据与规则冲突，降低置信度
- 置信度 < 0.5 的规则自动删除

## 实现计划

### Phase 1: 基础反馈收集（本周）
1. 创建 `feedback_tracker.py`
   - 记录反馈到 feedback.jsonl
   - 关键词识别
   - 隐式反馈推断

2. 集成到对话流程
   - 检测用户消息中的反馈关键词
   - 关联到最近的建议/行动

3. CLI 工具
   - 查看反馈统计
   - 手动添加反馈

### Phase 2: 统计分析（下周）
1. 创建 `feedback_analyzer.py`
   - 生成 feedback_stats.json
   - 按类别/时间/场景统计

2. 可视化报告
   - 每周生成反馈报告
   - 识别趋势

### Phase 3: 规则学习（2 周后）
1. 创建 `rule_learner.py`
   - 从反馈中提取规则
   - 生成 learned_rules.json

2. 规则应用
   - 在 Playbook 匹配前检查规则
   - 在生成建议前检查规则

3. 规则管理
   - 置信度更新
   - 规则冲突解决
   - 规则过期清理

## 成功指标

### 短期（1 周）
- 能够记录所有反馈
- 能够统计接受率
- 能够识别关键词反馈

### 中期（1 个月）
- 至少提取 5 条有效规则
- 建议接受率提升 10%
- 噪音建议减少 20%

### 长期（3 个月）
- 建议接受率 > 70%
- 自动学习的规则 > 20 条
- 用户满意度 > 4/5

## 隐私保护
- 所有反馈数据本地存储
- 不记录敏感内容
- 用户可随时查看/删除反馈记录

## 风险与对策

### 风险 1：过度学习
- **问题**：从少量反馈中得出错误结论
- **对策**：规则需要至少 5 次证据才生效

### 风险 2：规则冲突
- **问题**：新规则与旧规则矛盾
- **对策**：置信度高的规则优先，冲突时人工确认

### 风险 3：反馈稀疏
- **问题**：用户不经常给反馈
- **对策**：依赖隐式反馈，主动询问（低频）

## 下一步行动

1. ✅ 创建设计文档
2. ⏳ 实现 Phase 1: 基础反馈收集
   - 创建 `feedback_tracker.py`
   - 集成关键词识别
   - 测试反馈记录
3. ⏳ 运行 1 周积累数据
4. ⏳ 实现 Phase 2: 统计分析
5. ⏳ 实现 Phase 3: 规则学习

---

**文档版本**：v1.0  
**创建时间**：2026-02-23 15:04  
**作者**：小九  
**状态**：设计阶段
