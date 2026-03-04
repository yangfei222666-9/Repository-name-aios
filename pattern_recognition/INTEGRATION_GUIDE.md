# AIOS Pattern Recognition 集成指南

## 完成内容

### ✅ Phase 4: 集成到AIOS

**1. PatternRecognizer Agent**
- 文件：`aios/agent_system/agents/pattern_recognizer_agent.py`
- 功能：
  - 运行模式识别分析
  - 检测模式转变
  - 自动发送告警（critical/high风险）
  - 返回推荐策略

**2. Scheduler Enhancement**
- 文件：`aios/agent_system/core/scheduler_enhancement.py`
- 功能：
  - 根据卦象调整任务接受策略
  - 动态调整任务优先级
  - 智能选择模型（haiku/sonnet/opus）
  - 提供推荐行动列表

**3. Heartbeat v6.0**
- 文件：`aios/agent_system/heartbeat_v6.py`
- 功能：
  - 每小时运行一次模式识别
  - 自动更新调度器策略
  - 发送告警到 alerts.jsonl
  - 记录模式变化历史

## 使用方式

### 1. 独立运行 PatternRecognizer Agent

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system\agents
python pattern_recognizer_agent.py
```

**输出示例：**
```
=== PatternRecognizer Agent 测试 ===

状态: success
消息: 当前卦象: 泰卦 (置信度: 91.7%, 风险: low)

当前卦象: 泰卦
置信度: 91.7%
风险等级: low
告警: False

推荐策略:
  优先级: growth
  模型偏好: opus
  风险容忍度: high
```

### 2. 测试 Scheduler Enhancement

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system\core
python scheduler_enhancement.py
```

**输出示例：**
```
=== Scheduler Enhancement 测试 ===

1. 更新当前卦象...
   状态: success
   消息: 当前卦象: 泰卦 (置信度: 91.7%, 风险: low)

2. 当前策略:
   卦象: 泰卦
   策略: growth
   风险容忍度: high
   模型偏好: opus

3. 测试任务决策:

   任务1: code (复杂度: complex, 风险: high)
     接受: True
     优先级: normal → high
     模型: opus

   任务2: fix (复杂度: simple, 风险: low)
     接受: True
     优先级: high → high
     模型: haiku

   任务3: monitor (复杂度: simple, 风险: low)
     接受: True
     优先级: low → low
     模型: haiku
```

### 3. 运行 Heartbeat v6.0

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python heartbeat_v6.py
```

**输出示例：**
```
AIOS Heartbeat v6.0 Started

[PATTERN] Running pattern recognition...
  Current Pattern: 泰卦
  Confidence: 91.7%
  Risk Level: low
  Strategy: growth
  Model Preference: opus
  Risk Tolerance: high

HEARTBEAT_OK

Heartbeat Completed
```

**如果检测到危机：**
```
[PATTERN] Running pattern recognition...
  Current Pattern: 否卦
  Confidence: 83.3%
  Risk Level: critical
  Strategy: defense
  Model Preference: haiku
  Risk Tolerance: zero
  [!] Alert: 🚨 系统进入危机状态: 否卦 (风险等级: critical)

HEARTBEAT_OK
```

## 集成到现有系统

### 方案1：集成到 AgentManager

```python
# aios/agent_system/core/agent_manager.py

from scheduler_enhancement import SchedulerEnhancement

class AgentManager:
    def __init__(self):
        # ... 原有代码 ...
        self.scheduler_enhancer = SchedulerEnhancement()
    
    def create_agent(self, template_name: str, task_description: str = None):
        # 更新卦象
        self.scheduler_enhancer.update_pattern()
        
        # 根据策略调整任务
        task = {
            "type": template_name,
            "priority": "normal",
            "complexity": "medium",
            "risk": "medium",
        }
        
        # 判断是否接受任务
        if not self.scheduler_enhancer.should_accept_task(task):
            print(f"[SCHEDULER] Task rejected by pattern strategy")
            return None
        
        # 调整优先级
        adjusted_priority = self.scheduler_enhancer.adjust_task_priority(task)
        
        # 选择模型
        model = self.scheduler_enhancer.select_model(task)
        
        # ... 创建 Agent ...
```

### 方案2：集成到 Heartbeat

**修改 HEARTBEAT.md：**

```markdown
## Heartbeat v6.0 - 集成模式识别

每小时运行一次模式识别，根据卦象调整系统策略。

### 执行方式

```bash
cd C:\Users\A\.openclaw\workspace\aios\agent_system
python heartbeat_v6.py
```

### 功能

1. **模式识别** - 每小时分析系统状态
2. **策略调整** - 自动更新调度器策略
3. **告警发送** - 检测到危机时发送告警
4. **历史记录** - 记录模式变化历史
```

**在 OpenClaw 主会话心跳中调用：**

```bash
& "C:\Program Files\Python312\python.exe" -X utf8 C:\Users\A\.openclaw\workspace\aios\agent_system\heartbeat_v6.py
```

### 方案3：集成到 Cron

创建定时任务，每小时运行一次：

```json
{
  "name": "AIOS Pattern Recognition",
  "schedule": {
    "kind": "cron",
    "expr": "0 * * * *",
    "tz": "Asia/Shanghai"
  },
  "payload": {
    "kind": "systemEvent",
    "text": "cd C:\\Users\\A\\.openclaw\\workspace\\aios\\agent_system; python heartbeat_v6.py"
  },
  "sessionTarget": "main",
  "enabled": true
}
```

## 策略应用示例

### 泰卦（顺利期）

**系统状态：**
- 成功率：90%
- 增长率：+30%
- 稳定性：80%

**调度策略：**
- ✅ 接受所有任务（包括高风险）
- ✅ 复杂任务优先级提升
- ✅ 使用 opus 模型
- ✅ 尝试挑战性项目

**示例：**
```python
task = {"type": "code", "complexity": "complex", "risk": "high"}
accept = True  # 接受
priority = "high"  # 提升优先级
model = "opus"  # 使用高性能模型
```

### 否卦（危机期）

**系统状态：**
- 成功率：20%
- 增长率：-30%
- 稳定性：30%

**调度策略：**
- ❌ 拒绝高风险任务
- ✅ 只接受修复和监控任务
- ✅ 使用 haiku 模型（快速）
- ✅ 暂停新开发

**示例：**
```python
task1 = {"type": "code", "complexity": "complex", "risk": "high"}
accept = False  # 拒绝

task2 = {"type": "fix", "complexity": "simple", "risk": "low"}
accept = True  # 接受
priority = "high"  # 提升优先级
model = "haiku"  # 使用快速模型
```

### 屯卦（困难期）

**系统状态：**
- 成功率：50%
- 增长率：0%
- 稳定性：30%

**调度策略：**
- ⚠️ 只接受低风险任务
- ✅ 降低任务复杂度
- ✅ 使用 haiku 模型
- ✅ 增加重试次数

**示例：**
```python
task = {"type": "code", "complexity": "medium", "risk": "medium"}
accept = True  # 接受（但会降低复杂度）
priority = "normal"  # 保持原优先级
model = "haiku"  # 使用快速模型
```

## 告警机制

### 告警触发条件

1. **模式转变到高风险状态**
   - 任何卦象 → 否卦（critical）
   - 任何卦象 → 屯卦（high）

2. **当前就是高风险状态**
   - 首次检测到否卦
   - 首次检测到屯卦

### 告警格式

```json
{
  "timestamp": "2026-03-03T17:00:00",
  "level": "critical",
  "title": "系统状态变化: 否卦",
  "body": "🚨 系统进入危机状态: 否卦 (风险等级: critical)",
  "sent": false
}
```

### 告警处理

告警会写入 `aios/agent_system/alerts.jsonl`，由现有的告警系统处理（发送到 Telegram）。

## 状态持久化

### heartbeat_state.json

```json
{
  "last_pattern_check": "2026-03-03T17:00:00",
  "pattern_check_interval_hours": 1,
  "last_pattern": "泰卦",
  "pattern_change_count": 3
}
```

### pattern_history.jsonl

```json
{
  "timestamp": "2026-03-03T17:00:00",
  "status": "success",
  "primary_pattern": {
    "name": "泰卦",
    "confidence": 0.917,
    "risk_level": "low"
  },
  "system_metrics": {
    "success_rate": 0.9,
    "growth_rate": 0.3,
    "stability": 0.8,
    "resource_usage": 0.4
  },
  "recommended_strategy": {
    "priority": "growth",
    "model_preference": "opus",
    "risk_tolerance": "high"
  }
}
```

## 监控和调试

### 查看当前卦象

```bash
cd C:\Users\A\.openclaw\workspace\aios\pattern_recognition
python pattern_cli.py analyze
```

### 查看历史模式

```bash
python pattern_cli.py history 24
```

### 检测模式转变

```bash
python pattern_cli.py shift
```

### 模拟系统状态

```bash
# 模拟顺利期
python pattern_cli.py simulate 0.9 0.3 0.8 0.4

# 模拟危机期
python pattern_cli.py simulate 0.2 -0.3 0.3 0.8
```

## 性能影响

### 资源消耗

- **CPU：** 每次运行 <1秒
- **内存：** <50MB
- **磁盘：** 每次运行写入 ~1KB（pattern_history.jsonl）

### 运行频率

- **默认：** 每小时1次
- **可调整：** 修改 `pattern_check_interval_hours`

### 对系统的影响

- **最小化：** 只在心跳时运行，不阻塞主流程
- **异步：** 不影响任务执行
- **可选：** 可以随时禁用

## 下一步

### Phase 5: 完善策略（可选）

1. **更细粒度的策略**
   - 根据任务类型定制策略
   - 根据 Agent 历史表现调整

2. **自适应阈值**
   - 根据系统表现动态调整风险容忍度
   - 学习最优策略

3. **预测性维护**
   - 预测未来趋势
   - 提前预警

### Phase 6: 可视化（可选）

1. **Dashboard 集成**
   - 显示当前卦象
   - 显示历史趋势图
   - 显示策略调整记录

2. **实时监控**
   - WebSocket 推送卦象变化
   - 实时显示推荐策略

---

**版本：** v1.0  
**最后更新：** 2026-03-03  
**维护者：** 小九 + 珊瑚海
