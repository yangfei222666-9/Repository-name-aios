"""
分析性能数据
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def analyze_performance_data():
    """分析性能数据文件"""
    data_file = Path(__file__).parent / "data" / "performance_stats.jsonl"
    
    if not data_file.exists():
        print("❌ 性能数据文件不存在")
        return
    
    # 读取数据
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    if not records:
        print("❌ 没有性能数据")
        return
    
    print("=" * 60)
    print(f"AIOS 性能数据分析")
    print(f"数据文件: {data_file}")
    print(f"记录数量: {len(records)}")
    print("=" * 60)
    
    # 分析心跳性能
    durations = [r["duration_ms"] for r in records if "duration_ms" in r]
    
    if durations:
        durations_sorted = sorted(durations)
        
        print(f"\n📊 心跳性能统计（{len(durations)} 次）:")
        print(f"   平均: {sum(durations)/len(durations):.1f}ms")
        print(f"   最快: {min(durations):.1f}ms")
        print(f"   最慢: {max(durations):.1f}ms")
        print(f"   中位数: {durations_sorted[len(durations)//2]:.1f}ms")
        print(f"   P95: {durations_sorted[int(len(durations)*0.95)]:.1f}ms")
        print(f"   P99: {durations_sorted[int(len(durations)*0.99)]:.1f}ms")
        
        # 性能分布
        print(f"\n📈 性能分布:")
        ranges = [
            (0, 10, "< 10ms"),
            (10, 50, "10-50ms"),
            (50, 100, "50-100ms"),
            (100, 200, "100-200ms"),
            (200, float('inf'), "> 200ms")
        ]
        
        for min_val, max_val, label in ranges:
            count = sum(1 for d in durations if min_val <= d < max_val)
            pct = count / len(durations) * 100 if durations else 0
            bar = "█" * int(pct / 2)
            print(f"   {label:12} {count:4d} ({pct:5.1f}%) {bar}")
        
        # 时间趋势
        print(f"\n📉 时间趋势（最近 10 次）:")
        for i, record in enumerate(records[-10:], 1):
            ts = record.get("timestamp", "")
            duration = record.get("duration_ms", 0)
            result = record.get("result", "")
            
            # 提取时间部分
            if "T" in ts:
                time_part = ts.split("T")[1][:8]
            else:
                time_part = ts
            
            print(f"   {i:2d}. [{time_part}] {duration:6.1f}ms - {result}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    analyze_performance_data()
