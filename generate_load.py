#!/usr/bin/env python3
"""生成测试负载，让 AIOS 控制台有数据显示"""

import json
import time
from pathlib import Path
from datetime import datetime

def generate_test_events():
    """生成一些测试事件"""
    events_file = Path(__file__).parent / 'data' / 'events.jsonl'
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    event_types = [
        ('error', 'high_cpu_usage', {'cpu_percent': 85, 'threshold': 80}),
        ('error', 'memory_pressure', {'memory_percent': 78, 'threshold': 75}),
        ('warning', 'slow_response', {'latency_ms': 3500, 'threshold': 3000}),
        ('info', 'task_completed', {'task_id': 'test_001', 'duration_ms': 1200}),
        ('error', 'timeout', {'task_id': 'test_002', 'timeout_ms': 5000}),
        ('error', 'high_cpu_usage', {'cpu_percent': 88, 'threshold': 80}),
        ('warning', 'disk_usage_high', {'disk_percent': 82, 'threshold': 80}),
        ('info', 'agent_spawned', {'agent_id': 'test_agent_001', 'type': 'coder'}),
    ]
    
    print(f"📝 生成测试事件到: {events_file}")
    
    for i, (level, event_type, context) in enumerate(event_types, 1):
        event = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'event_type': event_type,
            'context': context,
            'source': 'load_generator'
        }
        
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        print(f"  {i}/{len(event_types)}: {level.upper():8} {event_type}")
        time.sleep(0.3)
    
    print(f"\n✅ 已生成 {len(event_types)} 个测试事件")
    print(f"📊 刷新控制台查看数据")

if __name__ == '__main__':
    generate_test_events()
