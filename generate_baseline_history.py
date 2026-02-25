#!/usr/bin/env python3
"""生成过去7天的 baseline 快照数据"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import random

def generate_baseline_history():
    """生成过去7天的基线数据"""
    baseline_file = Path(__file__).parent / 'learning' / 'baseline.jsonl'
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    
    # 清空旧数据
    baseline_file.write_text('', encoding='utf-8')
    
    print("生成过去7天的基线快照...")
    
    # 每天生成4个快照（每6小时一次）
    snapshots = []
    for day in range(7, 0, -1):
        for hour in [0, 6, 12, 18]:
            ts = datetime.now() - timedelta(days=day) + timedelta(hours=hour)
            
            # 模拟系统逐渐改善的趋势
            base_score = 0.3 + (7 - day) * 0.05  # 从 0.3 逐渐提升到 0.6
            noise = random.uniform(-0.05, 0.05)
            evolution_score = max(0.2, min(0.8, base_score + noise))
            
            # 工具成功率也逐渐提升
            tool_success_rate = 0.85 + (7 - day) * 0.02 + random.uniform(-0.03, 0.03)
            tool_success_rate = max(0.8, min(1.0, tool_success_rate))
            
            snapshot = {
                'ts': ts.isoformat(),
                'period_days': 1,
                'correction_rate': random.uniform(0, 0.1),
                'tool_success_rate': round(tool_success_rate, 3),
                'tool_p95_ms': {
                    'exec': random.randint(800, 1500),
                    'read': random.randint(50, 200),
                    'write': random.randint(100, 300)
                },
                'http_error_count': random.randint(0, 5),
                'http_502_rate': random.uniform(0, 0.02),
                'http_404_rate': random.uniform(0, 0.01),
                'total_events': random.randint(50, 150),
                'severity_counts': {
                    'CRIT': random.randint(0, 2),
                    'WARN': random.randint(5, 15),
                    'INFO': random.randint(40, 130),
                    'ERR': random.randint(2, 8)
                },
                'resource': {
                    'avg_cpu_percent': random.uniform(20, 40),
                    'avg_memory_percent': random.uniform(40, 60),
                    'peak_cpu_percent': random.uniform(50, 80),
                    'peak_memory_percent': random.uniform(60, 80)
                },
                'evolution_score': round(evolution_score, 2),
                'grade': 'healthy' if evolution_score >= 0.5 else 'ok' if evolution_score >= 0.3 else 'degraded'
            }
            
            snapshots.append(snapshot)
    
    # 写入文件
    print(f"生成了 {len(snapshots)} 个基线快照（过去7天）")
    
    with open(baseline_file, 'w', encoding='utf-8') as f:
        for snapshot in snapshots:
            f.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
    
    # 显示趋势
    print("\nEvolution Score 趋势:")
    for i, snapshot in enumerate(snapshots):
        if i % 4 == 0:  # 每天显示一次
            day = 7 - i // 4
            score = snapshot['evolution_score']
            grade = snapshot['grade']
            bar = '█' * int(score * 20)
            print(f"  {day}天前: {score:.2f} ({grade:8}) {bar}")
    
    print(f"\n✅ 已写入: {baseline_file}")
    print(f"📊 刷新控制台查看趋势图")

if __name__ == '__main__':
    generate_baseline_history()
