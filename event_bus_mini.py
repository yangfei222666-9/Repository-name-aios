#!/usr/bin/env python3
"""
AIOS EventBus - 最小实现（50 行核心代码）
统一所有事件，解耦模块
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class EventBus:
    """事件总线 - 最小实现"""
    
    def __init__(self, log_file=None):
        self.subscribers = defaultdict(list)
        self.log_file = log_file or Path(__file__).parent / "events" / "bus.jsonl"
    
    def emit(self, event_type: str, **data):
        """发射事件"""
        event = {
            "type": event_type,
            "ts": datetime.now().isoformat(),
            **data
        }
        
        # 持久化
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        # 通知订阅者
        for callback in self.subscribers[event_type]:
            try:
                callback(event)
            except Exception as e:
                print(f"❌ {e}")
    
    def on(self, event_type: str, callback):
        """订阅事件"""
        self.subscribers[event_type].append(callback)

# 全局单例
_bus = EventBus()

def emit(event_type: str, **data):
    """发射事件（全局函数）"""
    _bus.emit(event_type, **data)

def on(event_type: str, callback):
    """订阅事件（全局函数）"""
    _bus.on(event_type, callback)

# 使用示例
if __name__ == '__main__':
    # 订阅
    on("task.started", lambda e: print(f"📝 任务开始: {e}"))
    on("task.failed", lambda e: print(f"❌ 任务失败: {e}"))
    
    # 发射
    emit("task.started", task_id="t001", agent="coder")
    emit("task.failed", task_id="t001", error="timeout")
    
    print("✅ EventBus 测试完成")
