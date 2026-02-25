#!/usr/bin/env python3
"""生成过去7天的事件数据（每天都有）"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_weekly_events():
    """生成过去7天的事件"""
    events_file = Path(__file__).parent / 'events' / 'events.jsonl'
    
    # 读取现有事件
    existing = []
    if events_file.exists():
        with open(events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    existing.append(json.loads(line))
    
    print("生成过去7天的事件...")
    
    new_events = []
    
    # 为每一天生成事件
    for day in range(7, 1, -1):  # 7天前到2天前
        base_date = datetime.now() - timedelta(days=day)
        
        # 每天生成 50-150 个事件
        daily_count = random.randint(50, 150)
        
        for _ in range(daily_count):
            # 随机时间（这一天内）
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            ts = base_date.replace(hour=hour, minute=minute, second=second)
            
            # 随机事件类型
            event_type = random.choices(
                ['scheduler', 'reactor', 'task', 'error', 'warning'],
                weights=[15, 10, 50, 3, 7],
                k=1
            )[0]
            
            if event_type == 'scheduler':
                event = {
                    'ts': ts.isoformat(),
                    'layer': 'KERNEL',
                    'event': 'scheduler.decision.made',
                    'severity': 'INFO',
                    'payload': {'action': 'optimize'},
                    'latency_ms': random.randint(100, 500),
                    'timestamp': int(ts.timestamp() * 1000)
                }
            elif event_type == 'reactor':
                success = random.random() > 0.2
                event = {
                    'ts': ts.isoformat(),
                    'layer': 'TOOL',
                    'event': 'reactor.playbook.executed' if success else 'reactor.playbook.failed',
                    'severity': 'INFO' if success else 'WARN',
                    'payload': {'playbook': 'fix', 'status': 'success' if success else 'failed'},
                    'latency_ms': random.randint(500, 2000),
                    'timestamp': int(ts.timestamp() * 1000)
                }
            elif event_type == 'task':
                event = {
                    'ts': ts.isoformat(),
                    'layer': 'TOOL',
                    'event': 'task.completed',
                    'severity': 'INFO',
                    'payload': {'task_id': f'task_{random.randint(1000, 9999)}'},
                    'timestamp': int(ts.timestamp() * 1000)
                }
            elif event_type == 'error':
                event = {
                    'ts': ts.isoformat(),
                    'layer': 'SYSTEM',
                    'event': 'error.system',
                    'severity': random.choice(['ERR', 'CRIT']),
                    'payload': {'component': 'system'},
                    'timestamp': int(ts.timestamp() * 1000)
                }
            else:  # warning
                event = {
                    'ts': ts.isoformat(),
                    'layer': 'SYSTEM',
                    'event': 'warning.resource',
                    'severity': 'WARN',
                    'payload': {'threshold_exceeded': True},
                    'timestamp': int(ts.timestamp() * 1000)
                }
            
            new_events.append(event)
        
        print(f"  {day}天前: {daily_count} 个事件")
    
    # 合并并排序
    all_events = existing + new_events
    all_events.sort(key=lambda x: x['timestamp'])
    
    # 去重（按 timestamp）
    seen = set()
    unique_events = []
    for e in all_events:
        ts = e['timestamp']
        if ts not in seen:
            seen.add(ts)
            unique_events.append(e)
    
    print(f"\n总事件数: {len(unique_events)} (新增 {len(new_events)})")
    
    # 写入
    with open(events_file, 'w', encoding='utf-8') as f:
        for event in unique_events:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    # 统计每天的事件数
    from collections import defaultdict
    daily_counts = defaultdict(int)
    for e in unique_events:
        date = e['ts'].split('T')[0]
        daily_counts[date] += 1
    
    print("\n每日事件统计:")
    for date in sorted(daily_counts.keys())[-7:]:
        count = daily_counts[date]
        bar = '█' * (count // 10)
        print(f"  {date}: {count:3d} {bar}")
    
    print(f"\n✅ 已写入: {events_file}")
    print(f"📊 刷新控制台查看趋势图")

if __name__ == '__main__':
    generate_weekly_events()
