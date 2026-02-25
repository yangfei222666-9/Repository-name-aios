#!/usr/bin/env python3
"""生成一整天的 AIOS 事件，模拟真实运行"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_full_day_events():
    """生成24小时的事件数据"""
    events_file = Path(__file__).parent / 'events' / 'events.jsonl'
    events_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 保留现有事件
    existing_events = []
    if events_file.exists():
        with open(events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing_events.append(json.loads(line))
    
    events = []
    now = datetime.now()
    
    # 生成过去24小时的事件
    print("生成过去24小时的事件...")
    
    # 每小时生成一批事件
    for hour in range(24, 0, -1):
        base_time = now - timedelta(hours=hour)
        
        # 每小时的事件数量（模拟不同时段的活跃度）
        if 0 <= base_time.hour < 6:  # 深夜：少量事件
            event_count = random.randint(5, 10)
        elif 9 <= base_time.hour < 18:  # 工作时间：大量事件
            event_count = random.randint(20, 40)
        else:  # 其他时间：中等事件
            event_count = random.randint(10, 20)
        
        for _ in range(event_count):
            # 随机时间偏移（在这个小时内）
            offset_minutes = random.randint(0, 59)
            offset_seconds = random.randint(0, 59)
            ts = base_time + timedelta(minutes=offset_minutes, seconds=offset_seconds)
            
            # 随机选择事件类型
            event_type = random.choices(
                ['scheduler', 'reactor', 'task', 'error', 'warning'],
                weights=[15, 10, 50, 3, 7],  # 任务最多，错误最少
                k=1
            )[0]
            
            if event_type == 'scheduler':
                events.append({
                    'ts': ts.isoformat(),
                    'layer': 'KERNEL',
                    'event': 'scheduler.decision.made',
                    'severity': 'INFO',
                    'payload': {
                        'action': random.choice([
                            'optimize_agent_timeout',
                            'adjust_heartbeat_frequency',
                            'scale_agent_pool',
                            'rebalance_workload'
                        ]),
                        'reason': random.choice([
                            'high_failure_rate',
                            'resource_pressure',
                            'performance_degradation'
                        ])
                    },
                    'latency_ms': random.randint(100, 500),
                    'timestamp': int(ts.timestamp() * 1000)
                })
            
            elif event_type == 'reactor':
                success = random.random() > 0.2  # 80% 成功率
                events.append({
                    'ts': ts.isoformat(),
                    'layer': 'TOOL',
                    'event': 'reactor.playbook.executed' if success else 'reactor.playbook.failed',
                    'severity': 'INFO' if success else 'WARN',
                    'payload': {
                        'playbook': random.choice([
                            'fix_high_cpu',
                            'clear_memory',
                            'restart_agent',
                            'optimize_query'
                        ]),
                        'verified': success,
                        'status': 'success' if success else 'failed'
                    },
                    'latency_ms': random.randint(500, 2000),
                    'timestamp': int(ts.timestamp() * 1000)
                })
            
            elif event_type == 'task':
                events.append({
                    'ts': ts.isoformat(),
                    'layer': 'TOOL',
                    'event': 'task.completed',
                    'severity': 'INFO',
                    'payload': {
                        'task_id': f'task_{random.randint(1000, 9999)}',
                        'duration_ms': random.randint(500, 2000)
                    },
                    'timestamp': int(ts.timestamp() * 1000)
                })
            
            elif event_type == 'error':
                error_types = [
                    ('system_crash', 'CRIT'),
                    ('out_of_memory', 'ERR'),
                    ('disk_full', 'ERR'),
                    ('agent_failed', 'ERR'),
                    ('timeout', 'ERR')
                ]
                err_type, severity = random.choice(error_types)
                events.append({
                    'ts': ts.isoformat(),
                    'layer': 'SYSTEM',
                    'event': f'error.{err_type}',
                    'severity': severity,
                    'payload': {
                        'component': random.choice(['scheduler', 'reactor', 'agent', 'database']),
                        'details': f'{err_type} detected'
                    },
                    'timestamp': int(ts.timestamp() * 1000)
                })
            
            elif event_type == 'warning':
                warn_types = [
                    'high_cpu_usage',
                    'memory_pressure',
                    'slow_response',
                    'agent_timeout',
                    'disk_usage_high'
                ]
                events.append({
                    'ts': ts.isoformat(),
                    'layer': 'SYSTEM',
                    'event': f'warning.{random.choice(warn_types)}',
                    'severity': 'WARN',
                    'payload': {
                        'threshold_exceeded': True,
                        'value': random.randint(80, 95)
                    },
                    'timestamp': int(ts.timestamp() * 1000)
                })
    
    # 合并并排序
    all_events = existing_events + events
    all_events.sort(key=lambda x: x['timestamp'])
    
    # 统计
    total = len(events)
    crit = sum(1 for e in events if e['severity'] == 'CRIT')
    err = sum(1 for e in events if e['severity'] == 'ERR')
    warn = sum(1 for e in events if e['severity'] == 'WARN')
    info = sum(1 for e in events if e['severity'] == 'INFO')
    
    print(f"\n生成了 {total} 个新事件（过去24小时）")
    print(f"  - {crit} 个严重错误 (CRIT)")
    print(f"  - {err} 个错误 (ERR)")
    print(f"  - {warn} 个警告 (WARN)")
    print(f"  - {info} 个信息 (INFO)")
    print(f"\n总事件数: {len(all_events)}")
    
    # 写入文件
    print(f"\n写入到: {events_file}")
    with open(events_file, 'w', encoding='utf-8') as f:
        for event in all_events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    print(f"✅ 完成！刷新控制台查看数据")

if __name__ == '__main__':
    generate_full_day_events()
