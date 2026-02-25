# AIOS v0.5 从零搭建教程

本教程将带你从零开始搭建一个完整的AIOS系统，理解每个组件的作用和交互方式。

**预计时间：** 2-3小时  
**难度：** 中级  
**前置知识：** Python 3.12+、事件驱动架构基础

---

## 第1步：环境准备（10分钟）

### 1.1 安装依赖

```bash
# 克隆仓库
git clone https://github.com/your-username/aios.git
cd aios

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .
```

### 1.2 验证安装

```bash
# 运行测试
pytest aios/tests/ -v

# 应该看到：14 passed
```

---

## 第2步：理解EventBus（30分钟）

EventBus是AIOS的心脏，所有组件通过它通信。

### 2.1 创建第一个事件

创建 `tutorial/step1_eventbus.py`：

```python
from aios.core.event import Event
from aios.core.event_bus import EventBus

# 创建EventBus
bus = EventBus()

# 定义事件处理器
def handle_hello(event):
    print(f"收到事件: {event.type}")
    print(f"数据: {event.payload}")

# 订阅事件
bus.subscribe("hello", handle_hello)

# 发射事件
event = Event.create(
    event_type="hello",
    source="tutorial",
    payload={"message": "Hello AIOS!"}
)
bus.emit(event)
```

运行：
```bash
python tutorial/step1_eventbus.py
# 输出：
# 收到事件: hello
# 数据: {'message': 'Hello AIOS!'}
```

### 2.2 通配符订阅

```python
# 订阅所有resource事件
bus.subscribe("resource.*", handle_resource)

# 订阅所有事件
bus.subscribe("*", handle_all)
```

### 2.3 练习

创建一个简单的温度监控系统：
- 发射 `sensor.temperature` 事件
- 当温度 >80 时，发射 `alert.high_temperature` 事件
- 订阅并打印所有告警

---

## 第3步：搭建Scheduler（45分钟）

Scheduler负责决策：收到告警后，决定下一步做什么。

### 3.1 创建简单Scheduler

创建 `tutorial/step2_scheduler.py`：

```python
from aios.core.event import Event
from aios.core.event_bus import EventBus

class SimpleScheduler:
    def __init__(self, bus):
        self.bus = bus
        self.alerts = []
        
        # 订阅告警事件
        bus.subscribe("alert.*", self.handle_alert)
    
    def handle_alert(self, event):
        self.alerts.append(event)
        print(f"[Scheduler] 收到告警: {event.type}")
        
        # 决策逻辑
        if len(self.alerts) >= 3:
            print("[Scheduler] 告警过多，触发修复")
            self.bus.emit(Event.create(
                event_type="scheduler.decision",
                source="scheduler",
                payload={"action": "trigger_reactor"}
            ))
            self.alerts.clear()

# 使用
bus = EventBus()
scheduler = SimpleScheduler(bus)

# 模拟3个告警
for i in range(3):
    bus.emit(Event.create(
        event_type="alert.cpu_high",
        source="sensor",
        payload={"value": 95}
    ))
```

### 3.2 添加决策逻辑

扩展Scheduler，支持不同严重程度：

```python
def decide(self, alerts):
    # 按严重程度分类
    critical = [a for a in alerts if a.payload.get('severity') == 'critical']
    high = [a for a in alerts if a.payload.get('severity') == 'high']
    
    # 决策
    if len(critical) > 0:
        return {"action": "trigger_reactor", "priority": "high"}
    elif len(high) >= 3:
        return {"action": "trigger_reactor", "priority": "medium"}
    else:
        return {"action": "wait"}
```

### 3.3 练习

实现一个智能Scheduler：
- 支持3种决策：`trigger_reactor`、`wait`、`escalate`
- 考虑告警频率（避免过度反应）
- 添加冷却期（5分钟内不重复决策）

---

## 第4步：搭建Reactor（45分钟）

Reactor负责执行修复动作。

### 4.1 创建简单Reactor

创建 `tutorial/step3_reactor.py`：

```python
from aios.core.event import Event
from aios.core.event_bus import EventBus

class SimpleReactor:
    def __init__(self, bus):
        self.bus = bus
        self.executions = []
        
        # 订阅决策事件
        bus.subscribe("scheduler.decision", self.handle_decision)
    
    def handle_decision(self, event):
        action = event.payload.get('action')
        
        if action == "trigger_reactor":
            print("[Reactor] 执行修复...")
            success = self.execute_fix()
            
            # 发射结果
            self.bus.emit(Event.create(
                event_type="reactor.fix_completed",
                source="reactor",
                payload={"success": success}
            ))
    
    def execute_fix(self):
        # 模拟修复动作
        print("[Reactor] 降低进程优先级")
        print("[Reactor] 清理缓存")
        return True

# 使用
bus = EventBus()
reactor = SimpleReactor(bus)

# 触发修复
bus.emit(Event.create(
    event_type="scheduler.decision",
    source="scheduler",
    payload={"action": "trigger_reactor"}
))
```

### 4.2 添加Playbook规则

```python
class Reactor:
    def __init__(self, bus):
        self.bus = bus
        self.playbooks = {
            "cpu_high": {
                "name": "CPU峰值处理",
                "actions": ["降低优先级", "清理缓存"],
                "cooldown_minutes": 5
            },
            "memory_high": {
                "name": "内存高占用处理",
                "actions": ["清理缓存", "重启服务"],
                "cooldown_minutes": 10
            }
        }
    
    def match_playbook(self, alert_type):
        # 匹配规则
        if "cpu" in alert_type:
            return self.playbooks["cpu_high"]
        elif "memory" in alert_type:
            return self.playbooks["memory_high"]
        return None
```

### 4.3 添加熔断保护

```python
class CircuitBreaker:
    def __init__(self, threshold=3, timeout=300):
        self.failures = 0
        self.threshold = threshold
        self.timeout = timeout
        self.last_failure_time = 0
        self.is_open = False
    
    def call(self, func):
        if self.is_open:
            # 检查是否可以恢复
            if time.time() - self.last_failure_time > self.timeout:
                self.is_open = False
                self.failures = 0
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = func()
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.threshold:
                self.is_open = True
            
            raise e
```

### 4.4 练习

实现一个完整的Reactor：
- 支持多个Playbook规则
- 添加熔断保护（3次失败后熔断）
- 记录执行历史
- 验证修复结果

---

## 第5步：搭建ScoreEngine（30分钟）

ScoreEngine计算系统健康度评分。

### 5.1 创建简单ScoreEngine

创建 `tutorial/step4_score.py`：

```python
from aios.core.event import Event
from aios.core.event_bus import EventBus

class SimpleScoreEngine:
    def __init__(self, bus):
        self.bus = bus
        self.stats = {
            "success": 0,
            "failure": 0
        }
        self.current_score = 1.0
        
        # 订阅所有事件
        bus.subscribe("*", self.handle_event)
    
    def handle_event(self, event):
        # 统计成功/失败
        if event.type.endswith(".success"):
            self.stats["success"] += 1
        elif event.type.endswith(".failed"):
            self.stats["failure"] += 1
        
        # 每5个事件重新计算
        total = self.stats["success"] + self.stats["failure"]
        if total > 0 and total % 5 == 0:
            self.calculate_score()
    
    def calculate_score(self):
        total = self.stats["success"] + self.stats["failure"]
        if total == 0:
            return
        
        success_rate = self.stats["success"] / total
        self.current_score = success_rate
        
        print(f"[ScoreEngine] 当前评分: {self.current_score:.2f}")
        
        # 发射评分事件
        self.bus.emit(Event.create(
            event_type="score.updated",
            source="score_engine",
            payload={"score": self.current_score}
        ))
```

### 5.2 添加滑动窗口

```python
class ScoreEngine:
    WINDOW_SIZE = 100
    
    def __init__(self, bus):
        self.bus = bus
        self.recent_events = []  # 滑动窗口
    
    def handle_event(self, event):
        # 记录到滑动窗口
        self.recent_events.append(event)
        if len(self.recent_events) > self.WINDOW_SIZE:
            self.recent_events = self.recent_events[-self.WINDOW_SIZE:]
        
        # 基于窗口计算评分
        self.calculate_score()
    
    def calculate_score(self):
        window = self.recent_events
        if not window:
            return
        
        # 计算成功率
        successes = sum(1 for e in window if e.type.endswith(".success"))
        failures = sum(1 for e in window if e.type.endswith(".failed"))
        total = successes + failures
        
        success_rate = successes / total if total > 0 else 1.0
        self.current_score = success_rate
```

### 5.3 练习

实现完整的评分公式：
```python
score = success_rate * 0.4 + latency_score * 0.2 + stability * 0.2 + resource_margin * 0.2
```

---

## 第6步：整合所有组件（30分钟）

### 6.1 创建完整系统

创建 `tutorial/step5_full_system.py`：

```python
from aios.core.event_bus import EventBus
from aios.core.toy_scheduler import ToyScheduler
from aios.core.toy_reactor import ToyReactor
from aios.core.toy_score_engine import ToyScoreEngine

# 创建EventBus
bus = EventBus()

# 启动所有组件
scheduler = ToyScheduler(bus)
reactor = ToyReactor(bus)
score_engine = ToyScoreEngine(bus)

scheduler.start()
reactor.start()
score_engine.start()

print("AIOS系统已启动！")

# 模拟一些事件
import time
from aios.core.event import Event

# 发送资源告警
for i in range(5):
    bus.emit(Event.create(
        event_type="resource.cpu_high",
        source="sensor",
        payload={"value": 95}
    ))
    time.sleep(0.1)

# 等待处理
time.sleep(1)

# 查看评分
print(f"当前评分: {score_engine.get_score()}")
```

### 6.2 添加心跳机制

```python
import threading

def heartbeat_loop(bus):
    while True:
        # 每30秒发送心跳
        bus.emit(Event.create(
            event_type="system.heartbeat",
            source="heartbeat",
            payload={"timestamp": time.time()}
        ))
        time.sleep(30)

# 启动心跳线程
heartbeat_thread = threading.Thread(target=heartbeat_loop, args=(bus,))
heartbeat_thread.daemon = True
heartbeat_thread.start()
```

---

## 第7步：添加Memory Palace（20分钟）

### 7.1 使用Memory API

```python
from aios.memory.api import memory

# 存储教训
memory.store_lesson(
    category="timeout",
    pattern="network_error",
    lesson="增加重试机制，使用指数退避"
)

# 查找相似教训
results = memory.find_similar("超时")
for result in results:
    print(f"教训: {result['lesson']}")

# 建立关系
memory.link("timeout", "network_error", "causes")
```

### 7.2 集成到Reactor

```python
class SmartReactor(Reactor):
    def execute_fix(self, alert_type):
        # 查询历史教训
        lessons = memory.find_similar(alert_type)
        
        if lessons:
            print(f"[Reactor] 应用历史教训: {lessons[0]['lesson']}")
            # 根据教训执行修复
        else:
            print(f"[Reactor] 无历史教训，使用默认修复")
            # 执行默认修复
        
        # 记录新教训
        memory.store_lesson(
            category=alert_type,
            pattern="auto_fix",
            lesson="修复成功，记录到记忆宫殿"
        )
```

---

## 第8步：测试和验证（20分钟）

### 8.1 编写测试

创建 `tutorial/test_tutorial.py`：

```python
import unittest
from aios.core.event_bus import EventBus
from aios.core.event import Event

class TestTutorial(unittest.TestCase):
    def test_eventbus(self):
        bus = EventBus()
        received = []
        
        def handler(event):
            received.append(event)
        
        bus.subscribe("test", handler)
        bus.emit(Event.create("test", "tutorial", {}))
        
        self.assertEqual(len(received), 1)
    
    def test_full_flow(self):
        # 测试完整流程
        bus = EventBus()
        # ... 启动所有组件
        # ... 发送事件
        # ... 验证结果
        pass

if __name__ == '__main__':
    unittest.main()
```

### 8.2 运行测试

```bash
pytest tutorial/test_tutorial.py -v
```

---

## 第9步：部署和监控（15分钟）

### 9.1 启动Dashboard

```bash
python -m aios.dashboard
```

访问 `http://localhost:8080`

### 9.2 配置心跳

编辑 `HEARTBEAT.md`，添加自定义任务。

### 9.3 查看日志

```bash
# 查看事件日志
cat aios/data/events.jsonl

# 查看清理报告
cat aios/data/cleanup_report.json

# 查看知识提取报告
cat aios/data/knowledge_report.json
```

---

## 常见问题

**Q: EventBus没有收到事件？**
A: 检查订阅是否在发射之前。确保事件类型匹配。

**Q: Reactor不执行修复？**
A: 检查Scheduler是否发射了`scheduler.decision`事件。检查Playbook规则是否匹配。

**Q: ScoreEngine评分一直是1.0？**
A: 确保有足够的事件（至少5个）。检查事件类型是否包含`.success`或`.failed`。

**Q: Memory查询返回空？**
A: 确保已经存储了教训。检查查询关键词是否匹配。

---

## 下一步

恭喜！你已经搭建了一个完整的AIOS系统。

**进阶学习：**
1. 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 深入理解架构
2. 阅读 [API.md](API.md) 学习完整API
3. 贡献代码到 [GitHub](https://github.com/your-username/aios)
4. 加入社区 [Discord](https://discord.gg/aios)

**实战项目：**
1. 为你的应用添加AIOS监控
2. 编写自定义Playbook规则
3. 开发新的Memory后端（Chroma/Neo4j）
4. 创建ClawdHub技能

---

**版本：** v0.5  
**更新日期：** 2026-02-24  
**作者：** 珊瑚海 + 小九
