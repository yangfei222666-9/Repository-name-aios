#!/usr/bin/env python3
"""生成符合 AIOS 控制台格式的测试事件"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_aios_events():
    """生成符合 AIOS 格式的事件"""
    events_file = Path(__file__).parent / 'events' / 'events.jsonl'
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 清空旧数据
    events_file.write_text('', encoding='utf-8')
    
    # 生成不同层级的事件
    events = []
    
    # KERNEL 层决策事件
    for i in range(5):
        ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
        events.append({
            'ts': ts.isoformat(),
            'layer': 'KERNEL',
            'event': 'scheduler.decision.made',
            'severity': 'INFO',
            'payload': {
                'action': 'optimize_agent_timeout',
                'reason': 'high_failure_rate'
            },
            'latency_ms': random.randint(100, 500),
            'timestamp': int(ts.timestamp() * 1000)
        })
    
    # TOOL 层 Reactor 事件
    for i in range(3):
        ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
        events.append({
            'ts': ts.isoformat(),
            'layer': 'TOOL',
            'event': 'reactor.playbook.executed',
            'severity': 'INFO',
            'payload': {
                'playbook': 'fix_high_cpu',
                'verified': True
            },
            'latency_ms': random.randint(500, 2000),
            'timestamp': int(ts.timestamp() * 1000)
        })
    
    # 错误事件
    error_types = [
        ('system_crash', 'CRIT'),
        ('out_of_memory', 'ERR'),
        ('disk_full', 'ERR'),
    ]
    
    for event_type, severity in error_types:
        ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
        events.append({
            'ts': ts.isoformat(),
            'layer': 'SYSTEM',
            'event': f'error.{event_type}',
            'severity': severity,
            'payload': {
                'component': 'scheduler',
                'details': f'{event_type} detected'
            },
            'timestamp': int(ts.timestamp() * 1000)
        })
    
    # 警告事件
    warning_types = [
        'high_cpu_usage',
        'memory_pressure',
        'slow_response',
        'agent_timeout'
    ]
    
    for event_type in warning_types:
        ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
        events.append({
            'ts': ts.isoformat(),
            'layer': 'SYSTEM',
            'event': f'warning.{event_type}',
            'severity': 'WARN',
            'payload': {
                'threshold_exceeded': True
            },
            'timestamp': int(ts.timestamp() * 1000)
        })
    
    # 信息事件
    for i in range(10):
        ts = datetime.now() - timedelta(minutes=random.randint(0, 60))
        events.append({
            'ts': ts.isoformat(),
            'layer': 'TOOL',
            'event': 'task.completed',
            'severity': 'INFO',
            'payload': {
                'task_id': f'task_{i:03d}',
                'duration_ms': random.randint(500, 2000)
            },
            'timestamp': int(ts.timestamp() * 1000)
        })
    
    # 按时间排序
    events.sort(key=lambda x: x['timestamp'])
    
    # 写入文件
    print(f"生成 {len(events)} 个 AIOS 格式事件")
    print(f"  - {sum(1 for e in events if e['severity'] == 'CRIT')} 个严重错误")
    print(f"  - {sum(1 for e in events if e['severity'] == 'ERR')} 个错误")
    print(f"  - {sum(1 for e in events if e['severity'] == 'WARN')} 个警告")
    print(f"  - {sum(1 for e in events if e['severity'] == 'INFO')} 个信息")
    print()
    
    for i, event in enumerate(events, 1):
        with open(events_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        severity_emoji = {
            'CRIT': '🔴',
            'ERR': '🟠',
            'WARN': '🟡',
            'INFO': '🔵'
        }
        print(f"  {i:2d}/{len(events)}: {severity_emoji.get(event['severity'], '⚪')} {event['severity']:4} {event['event']}")
        time.sleep(0.05)
    
    print(f"\n✅ 已生成到: {events_file}")
    print(f"📊 刷新控制台查看数据")

if __name__ == '__main__':
    generate_aios_events()
