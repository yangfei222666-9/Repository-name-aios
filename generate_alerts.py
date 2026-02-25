#!/usr/bin/env python3
"""生成更多测试负载，包括会触发告警的事件"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_alerts():
    """生成会触发告警的事件"""
    events_file = Path(__file__).parent / 'data' / 'events.jsonl'
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 生成不同严重级别的事件
    critical_events = [
        ('error', 'system_crash', {'component': 'scheduler', 'exit_code': 1}),
        ('error', 'out_of_memory', {'memory_percent': 98, 'threshold': 90}),
        ('error', 'disk_full', {'disk_percent': 95, 'threshold': 90}),
    ]
    
    warning_events = [
        ('warning', 'high_cpu_usage', {'cpu_percent': 85, 'threshold': 80}),
        ('warning', 'slow_response', {'latency_ms': 4500, 'threshold': 3000}),
        ('warning', 'memory_pressure', {'memory_percent': 82, 'threshold': 75}),
        ('warning', 'agent_timeout', {'agent_id': 'coder_001', 'timeout_ms': 30000}),
    ]
    
    info_events = [
        ('info', 'task_completed', {'task_id': f'task_{i:03d}', 'duration_ms': random.randint(500, 2000)})
        for i in range(10)
    ]
    
    all_events = critical_events + warning_events + info_events
    
    print(f"生成 {len(all_events)} 个测试事件")
    print(f"  - {len(critical_events)} 个严重错误")
    print(f"  - {len(warning_events)} 个警告")
    print(f"  - {len(info_events)} 个信息")
    print()
    
    for i, (level, event_type, context) in enumerate(all_events, 1):
        # 随机分布时间（最近1小时内）
        timestamp = datetime.now() - timedelta(minutes=random.randint(0, 60))
        
        # 根据 event_type 推断 env（agent_timeout 看 agent_id）
        env = 'prod'
        if 'agent_id' in context:
            if 'test' in context['agent_id'].lower():
                env = 'test'
        
        event = {
            'timestamp': timestamp.isoformat(),
            'level': level,
            'event_type': event_type,
            'context': context,
            'source': 'load_generator_v2',
            'env': env  # 新增 env 标签
        }
        
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        severity_emoji = {'error': '🔴', 'warning': '🟡', 'info': '🔵'}
        print(f"  {i:2d}/{len(all_events)}: {severity_emoji.get(level, '⚪')} {level.upper():8} {event_type}")
        time.sleep(0.1)
    
    print(f"\n✅ 已生成 {len(all_events)} 个测试事件")
    print(f"📊 刷新控制台查看告警")

if __name__ == '__main__':
    generate_alerts()
