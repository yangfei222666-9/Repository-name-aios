#!/usr/bin/env python3
"""
AIOS Event Bus - 统一事件总线
所有模块通过事件通信，解耦架构
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Callable, Any
from collections import defaultdict
import threading

AIOS_ROOT = Path(__file__).parent
EVENT_LOG = AIOS_ROOT / "events" / "event_bus.jsonl"

class EventBus:
    """事件总线：发布-订阅模式"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)  # event_type -> [callbacks]
        self.lock = threading.Lock()
        self.event_history = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        with self.lock:
            self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable):
        """取消订阅"""
        with self.lock:
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)
    
    def emit(self, event_type: str, data: Dict[str, Any] = None):
        """发射事件"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        
        # 记录到历史
        with self.lock:
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
        
        # 持久化
        self._persist(event)
        
        # 通知订阅者
        callbacks = self.subscribers.get(event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"❌ Event callback error: {e}")
    
    def _persist(self, event: Dict):
        """持久化事件"""
        EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
        
        with open(EVENT_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def get_recent_events(self, event_type: str = None, limit: int = 100) -> List[Dict]:
        """获取最近的事件"""
        with self.lock:
            if event_type:
                events = [e for e in self.event_history if e['type'] == event_type]
            else:
                events = self.event_history
            
            return events[-limit:]

# 全局单例
_event_bus = None

def get_event_bus() -> EventBus:
    """获取全局事件总线"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus

# 便捷函数
def emit(event_type: str, data: Dict[str, Any] = None):
    """发射事件（便捷函数）"""
    get_event_bus().emit(event_type, data)

def subscribe(event_type: str, callback: Callable):
    """订阅事件（便捷函数）"""
    get_event_bus().subscribe(event_type, callback)

# 预定义事件类型
class EventType:
    """事件类型常量"""
    
    # Agent 生命周期
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_IDLE = "agent.idle"
    AGENT_RUNNING = "agent.running"
    AGENT_BLOCKED = "agent.blocked"
    AGENT_DEGRADED = "agent.degraded"
    AGENT_STOPPED = "agent.stopped"
    AGENT_FAILED = "agent.failed"
    
    # 任务事件
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_TIMEOUT = "task.timeout"
    
    # 资源事件
    RESOURCE_SPIKE = "resource.spike"
    RESOURCE_LOW = "resource.low"
    RESOURCE_CRITICAL = "resource.critical"
    
    # 系统事件
    SYSTEM_HEALTHY = "system.healthy"
    SYSTEM_DEGRADED = "system.degraded"
    SYSTEM_CRITICAL = "system.critical"
    
    # Pipeline 事件
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"
    
    # Reactor 事件
    REACTOR_TRIGGERED = "reactor.triggered"
    REACTOR_EXECUTED = "reactor.executed"
    REACTOR_FAILED = "reactor.failed"

# 示例：监听器
def example_listener(event: Dict):
    """示例事件监听器"""
    print(f"📨 收到事件: {event['type']}")
    print(f"   数据: {event['data']}")

if __name__ == '__main__':
    # 测试事件总线
    bus = get_event_bus()
    
    # 订阅事件
    bus.subscribe(EventType.TASK_STARTED, example_listener)
    bus.subscribe(EventType.TASK_COMPLETED, example_listener)
    
    # 发射事件
    print("🚀 测试事件总线\n")
    
    emit(EventType.TASK_STARTED, {
        "task_id": "task-001",
        "agent": "coder",
        "description": "编写代码"
    })
    
    time.sleep(0.1)
    
    emit(EventType.TASK_COMPLETED, {
        "task_id": "task-001",
        "duration_ms": 1500,
        "result": "success"
    })
    
    time.sleep(0.1)
    
    emit(EventType.RESOURCE_SPIKE, {
        "resource": "cpu",
        "value": 85,
        "threshold": 80
    })
    
    # 查询最近事件
    print(f"\n📊 最近事件数: {len(bus.get_recent_events())}")
    
    print("\n✅ 事件总线测试完成")
