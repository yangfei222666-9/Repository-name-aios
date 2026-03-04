# Pattern Recognition System - 使用指南

基于易经64卦理论的AIOS系统状态识别与策略推荐系统。

## 核心理念

**易经的智慧应用于AI系统：**
- **变化感知** - 监控系统指标的变化趋势（上升/下降/波动/稳定）
- **模式识别** - 将系统状态映射到64种"情境模板"（卦象）
- **策略推荐** - 根据当前"卦象"推荐应对策略

## 系统架构

```
ChangeDetector（变化检测）
    ↓
SystemChangeMonitor（系统监控）
    ↓
HexagramMatcher（卦象匹配）
    ↓
PatternRecognizer Agent（模式识别）
    ↓
策略推荐 + 风险评估
```

## 快速开始

### 1. 运行测试

```bash
cd C:\Users\A\.openclaw\workspace\aios\pattern_recognition
python test_pattern_recognition.py
```

**输出示例：**
```
【场景1：顺利期】
  匹配卦象: 泰卦 (第11卦)
  置信度: 91.67%
  风险等级: low
  推荐策略: growth

【场景2：危机期】
  匹配卦象: 否卦 (第12卦)
  置信度: 83.33%
  风险等级: critical
  推荐策略: defense
  建议行动: pause_new_tasks, fix_critical_bugs
```

### 2. 独立使用 ChangeDetector

```python
from change_detector import ChangeDetector

# 创建检测器
detector = ChangeDetector(window_size=10, threshold=0.1)

# 添加数据点
for value in [0.5, 0.55, 0.6, 0.65, 0.7]:
    detector.add_data_point(value)

# 检测趋势
trend, confidence = detector.detect_trend()
print(f"趋势: {trend}, 置信度: {confidence:.2%}")

# 获取摘要
summary = detector.get_summary()
print(summary)
```

### 3. 使用 HexagramMatcher

```python
from hexagram_patterns import HexagramMatcher

matcher = HexagramMatcher()

# 定义系统指标
metrics = {
    "success_rate": 0.9,      # 成功率 90%
    "growth_rate": 0.3,       # 增长率 30%
    "stability": 0.8,         # 稳定性 80%
    "resource_usage": 0.4,    # 资源使用 40%
}

# 匹配卦象
pattern, confidence = matcher.match(metrics)
print(f"当前卦象: {pattern.name}")
print(f"推荐策略: {pattern.strategy}")
```

### 4. 使用 PatternRecognizer Agent

```python
from pattern_recognizer import PatternRecognizerAgent

# 创建Agent
agent = PatternRecognizerAgent()

# 生成摘要报告
summary = agent.generate_summary_report()
print(summary)

# 获取详细报告
report = agent.analyze_current_state()
print(report)

# 检测模式转变
shift = agent.detect_pattern_shift()
if shift:
    print(f"检测到转变: {shift['from_pattern']} → {shift['to_pattern']}")
```

## 核心组件

### 1. ChangeDetector - 变化检测器

**功能：** 监控单个指标的变化趋势

**趋势类型：**
- `rising` - 上升期（泰卦）
- `falling` - 下降期（否卦）
- `volatile` - 波动期（屯卦）
- `stable` - 稳定期（恒卦）

**参数：**
- `window_size` - 滑动窗口大小（默认10）
- `threshold` - 变化阈值（默认0.1）

### 2. SystemChangeMonitor - 系统监控器

**功能：** 监控多个关键指标

**监控指标：**
- `success_rate` - 任务成功率
- `avg_duration` - 平均耗时
- `error_rate` - 错误率
- `cost` - 平均成本

**方法：**
- `load_recent_tasks(hours)` - 加载最近N小时的任务
- `update_from_tasks(tasks)` - 从任务数据更新检测器
- `get_all_trends()` - 获取所有指标的趋势
- `get_overall_state()` - 获取系统整体状态（简化版卦象）

### 3. HexagramMatcher - 卦象匹配器

**功能：** 将系统状态映射到64卦

**核心卦象：**
1. **乾卦** - 高成功率、快速增长、高稳定性 → 扩张策略
2. **坤卦** - 平稳增长、极高稳定性 → 稳定策略
3. **屯卦** - 中低成功率、低稳定性 → 生存策略
4. **泰卦** - 高成功率、快速增长 → 增长策略
5. **否卦** - 低成功率、负增长 → 防守策略
6. **恒卦** - 平稳状态、高稳定性 → 维护策略

**方法：**
- `match(metrics)` - 匹配最接近的卦象
- `get_top_matches(metrics, top_n)` - 获取前N个最匹配的卦象

### 4. PatternRecognizer Agent - 模式识别Agent

**功能：** 完整的系统状态分析和策略推荐

**核心方法：**
- `analyze_current_state()` - 分析当前系统状态
- `generate_summary_report()` - 生成人类可读的摘要报告
- `detect_pattern_shift()` - 检测模式转变（卦象变化）
- `get_recent_patterns(hours)` - 获取最近的模式历史

## 64卦映射表

### 第一组：创业期（1-8卦）

| 卦序 | 卦名 | 系统状态 | 推荐策略 | 风险等级 |
|------|------|----------|----------|----------|
| 1 | 乾卦 | 高成功率、快速增长 | 扩张优先 | low |
| 2 | 坤卦 | 平稳增长、极高稳定性 | 稳定优先 | low |
| 3 | 屯卦 | 中低成功率、低稳定性 | 生存优先 | high |
| 4 | 蒙卦 | 学习阶段 | 学习优先 | medium |
| 5 | 需卦 | 等待资源 | 耐心等待 | low |
| 6 | 讼卦 | 检测到冲突 | 解决冲突 | critical |
| 7 | 师卦 | 团队协作 | 协调优先 | medium |
| 8 | 比卦 | 协作良好 | 联盟优先 | low |

### 第二组：发展期（9-16卦）

| 卦序 | 卦名 | 系统状态 | 推荐策略 | 风险等级 |
|------|------|----------|----------|----------|
| 11 | 泰卦 | 高成功率、快速增长 | 增长优先 | low |
| 12 | 否卦 | 低成功率、负增长 | 防守优先 | critical |
| 32 | 恒卦 | 平稳状态、高稳定性 | 维护优先 | low |

*（完整64卦映射见 `hexagram_patterns.py`）*

## 策略推荐

### 泰卦（顺利期）

**系统状态：**
- 成功率：80-100%
- 增长率：20-50%
- 稳定性：70-90%

**推荐策略：**
- 优先级：growth（增长）
- 模型偏好：opus（高性能）
- 风险容忍度：high
- 建议行动：
  - 扩大运营规模
  - 尝试雄心勃勃的项目
  - 投资创新

### 否卦（危机期）

**系统状态：**
- 成功率：0-40%
- 增长率：-50% ~ -10%
- 稳定性：10-40%

**推荐策略：**
- 优先级：defense（防守）
- 模型偏好：haiku（快速）
- 风险容忍度：zero
- 建议行动：
  - 暂停新任务
  - 修复关键Bug
  - 回滚到稳定版本
  - 进入紧急模式

### 屯卦（困难期）

**系统状态：**
- 成功率：30-60%
- 增长率：-20% ~ 20%
- 稳定性：20-50%

**推荐策略：**
- 优先级：survival（生存）
- 模型偏好：haiku（快速）
- 风险容忍度：very_low
- 建议行动：
  - 降低任务复杂度
  - 增加重试次数
  - 寻求外部帮助
  - 专注核心任务

### 恒卦（稳定期）

**系统状态：**
- 成功率：70-90%
- 增长率：-5% ~ 5%
- 稳定性：80-100%

**推荐策略：**
- 优先级：maintenance（维护）
- 模型偏好：sonnet（平衡）
- 风险容忍度：low
- 建议行动：
  - 保持稳定状态
  - 渐进式改进
  - 常规优化

## 集成到AIOS

### 方案1：新增 PatternRecognizer Agent

```python
# aios/agent_system/agents/pattern_recognizer.py
from aios.pattern_recognition.pattern_recognizer import PatternRecognizerAgent

class PatternRecognizerAgentWrapper:
    def __init__(self):
        self.agent = PatternRecognizerAgent()
    
    def run(self):
        # 生成报告
        report = self.agent.analyze_current_state()
        
        # 检测模式转变
        shift = self.agent.detect_pattern_shift()
        
        # 如果检测到转变，发送通知
        if shift and shift.get("to_risk") == "critical":
            self.send_alert(shift)
        
        return report
```

### 方案2：增强 Scheduler 决策

```python
# aios/agent_system/scheduler.py
from aios.pattern_recognition.pattern_recognizer import PatternRecognizerAgent

class Scheduler:
    def __init__(self):
        self.pattern_recognizer = PatternRecognizerAgent()
    
    def decide_next_task(self):
        # 获取当前卦象
        report = self.pattern_recognizer.analyze_current_state()
        current_pattern = report.get("primary_pattern", {}).get("name")
        
        # 根据卦象调整决策
        if current_pattern == "否卦":
            # 危机期：只执行低风险任务
            return self.get_safe_tasks()
        elif current_pattern == "泰卦":
            # 顺利期：可以尝试高风险高回报任务
            return self.get_challenging_tasks()
        else:
            # 正常决策
            return self.get_normal_tasks()
```

### 方案3：集成到 Heartbeat

```python
# HEARTBEAT.md
def heartbeat():
    # ... 其他检查 ...
    
    # 每小时运行一次模式识别
    if should_run_pattern_recognition():
        agent = PatternRecognizerAgent()
        report = agent.analyze_current_state()
        
        # 如果风险等级为 critical，发送通知
        if report.get("primary_pattern", {}).get("risk_level") == "critical":
            send_telegram_alert(report)
```

## 实际价值

1. **自适应调整** - 系统根据"势"自动调整策略，不需要人工干预
2. **风险控制** - 在"否卦"（危机期）自动收缩，避免雪崩
3. **机会把握** - 在"泰卦"（顺利期）大胆尝试，加速成长
4. **可解释性** - "当前处于屯卦，所以降低任务复杂度"比"算法决定"更容易理解
5. **预测性维护** - 检测到"泰卦→否卦"转变时提前预警

## 下一步

### Phase 4: 完善64卦映射（可选）

当前只实现了8个核心卦象，可以扩展到完整的64卦：

```python
# 添加更多卦象
9: HexagramPattern(name="小畜卦", ...),
10: HexagramPattern(name="履卦", ...),
13: HexagramPattern(name="同人卦", ...),
# ... 共64个
```

### Phase 5: 历史分析

```python
def analyze_pattern_evolution(days=7):
    """分析过去N天的卦象演变"""
    patterns = agent.get_recent_patterns(hours=days*24)
    
    # 统计卦象分布
    # 识别周期性模式
    # 预测未来趋势
```

### Phase 6: 自动化决策

```python
def auto_adjust_strategy():
    """根据卦象自动调整系统参数"""
    report = agent.analyze_current_state()
    strategy = report["recommended_strategy"]
    
    # 自动切换模型
    if strategy["model_preference"] == "opus":
        switch_to_opus()
    
    # 自动调整风险容忍度
    if strategy["risk_tolerance"] == "zero":
        enable_emergency_mode()
```

## 文件结构

```
aios/pattern_recognition/
├── change_detector.py          # 变化检测器
├── hexagram_patterns.py        # 64卦映射表
├── pattern_recognizer.py       # 模式识别Agent
├── test_pattern_recognition.py # 测试脚本
└── PATTERN_RECOGNITION_GUIDE.md # 本文档
```

## 常见问题

### Q1: 为什么选择易经64卦？

**A:** 易经64卦是一套完整的"情境分类系统"，经过几千年验证。它的核心价值不是"算命"，而是：
1. **模式识别** - 64种情境模板覆盖了大部分常见场景
2. **变化感知** - 强调"势"的转变，而不只是当前状态
3. **策略推荐** - 每个卦象都有对应的应对策略
4. **可解释性** - "当前处于泰卦"比"置信度0.87"更容易理解

### Q2: 如何选择合适的卦象？

**A:** HexagramMatcher 使用多维度匹配算法：
1. 计算系统指标（成功率、增长率、稳定性、资源使用）
2. 与每个卦象的状态特征进行匹配
3. 计算匹配分数（0-1）
4. 返回最高分的卦象

### Q3: 如何处理边界情况？

**A:** 系统提供前3个最匹配的卦象，而不只是最佳匹配：
```python
top_matches = matcher.get_top_matches(metrics, top_n=3)
# [(泰卦, 0.92), (乾卦, 0.85), (恒卦, 0.78)]
```

如果前3个卦象的置信度都很接近，说明系统处于"过渡期"，可以综合考虑多个策略。

### Q4: 如何验证系统有效性？

**A:** 三种验证方式：
1. **回测** - 用历史数据验证卦象匹配是否准确
2. **A/B测试** - 对比使用/不使用模式识别的系统表现
3. **人工审核** - 定期检查推荐策略是否合理

---

**版本：** v1.0  
**最后更新：** 2026-03-03  
**维护者：** 小九 + 珊瑚海
