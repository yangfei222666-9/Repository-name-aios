"""
AIOS 长期性能监控
收集 1 周性能数据，生成趋势报告
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_long_term_performance():
    """分析长期性能数据"""
    data_file = Path(__file__).parent / "data" / "performance_stats.jsonl"
    
    if not data_file.exists():
        print("❌ 性能数据文件不存在")
        return
    
    # 读取数据
    records = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except:
                    pass
    
    if not records:
        print("❌ 没有性能数据")
        return
    
    print("=" * 60)
    print(f"AIOS 长期性能分析")
    print(f"数据文件: {data_file}")
    print(f"记录数量: {len(records)}")
    print("=" * 60)
    
    # 按日期分组
    daily_data = defaultdict(list)
    for record in records:
        ts = record.get("timestamp", "")
        if "T" in ts:
            date = ts.split("T")[0]
            duration = record.get("duration_ms", 0)
            daily_data[date].append(duration)
    
    # 每日统计
    print(f"\n📊 每日性能统计:")
    print(f"{'日期':<12} {'样本数':>6} {'平均':>8} {'最快':>8} {'最慢':>8} {'P95':>8}")
    print("-" * 60)
    
    for date in sorted(daily_data.keys())[-7:]:  # 最近 7 天
        durations = daily_data[date]
        durations_sorted = sorted(durations)
        
        avg = sum(durations) / len(durations)
        min_val = min(durations)
        max_val = max(durations)
        p95 = durations_sorted[int(len(durations) * 0.95)]
        
        print(f"{date:<12} {len(durations):>6} {avg:>7.1f}ms {min_val:>7.1f}ms {max_val:>7.1f}ms {p95:>7.1f}ms")
    
    # 趋势分析
    print(f"\n📈 性能趋势:")
    
    dates = sorted(daily_data.keys())[-7:]
    if len(dates) >= 2:
        first_day = daily_data[dates[0]]
        last_day = daily_data[dates[-1]]
        
        first_avg = sum(first_day) / len(first_day)
        last_avg = sum(last_day) / len(last_day)
        
        change = last_avg - first_avg
        change_pct = (change / first_avg) * 100 if first_avg != 0 else 0
        
        if change < 0:
            print(f"   ✅ 性能改善: {abs(change):.1f}ms ({abs(change_pct):.1f}%)")
        elif change > 0:
            print(f"   ⚠️ 性能下降: {change:.1f}ms ({change_pct:.1f}%)")
        else:
            print(f"   ➡️ 性能稳定")
    
    # 异常检测
    print(f"\n⚠️ 异常检测:")
    
    all_durations = []
    for durations in daily_data.values():
        all_durations.extend(durations)
    
    avg = sum(all_durations) / len(all_durations)
    threshold = avg * 3  # 3倍平均值
    
    anomalies = [d for d in all_durations if d > threshold]
    
    if anomalies:
        print(f"   发现 {len(anomalies)} 个异常值（> {threshold:.1f}ms）")
        print(f"   异常占比: {len(anomalies)/len(all_durations)*100:.2f}%")
    else:
        print(f"   ✅ 无异常值")
    
    # 性能分级
    print(f"\n🎯 性能分级:")
    
    excellent = sum(1 for d in all_durations if d < 5)
    good = sum(1 for d in all_durations if 5 <= d < 10)
    acceptable = sum(1 for d in all_durations if 10 <= d < 50)
    poor = sum(1 for d in all_durations if d >= 50)
    
    total = len(all_durations)
    
    if total > 0:
        print(f"   优秀 (< 5ms):    {excellent:5d} ({excellent/total*100:5.1f}%)")
        print(f"   良好 (5-10ms):   {good:5d} ({good/total*100:5.1f}%)")
        print(f"   可接受 (10-50ms): {acceptable:5d} ({acceptable/total*100:5.1f}%)")
        print(f"   较差 (> 50ms):   {poor:5d} ({poor/total*100:5.1f}%)")
    else:
        print("   无数据")
    
    # 建议
    print(f"\n💡 优化建议:")
    
    if avg < 5:
        print(f"   ✅ 性能优秀，无需优化")
    elif avg < 10:
        print(f"   ✅ 性能良好，可继续监控")
    elif avg < 50:
        print(f"   ⚠️ 性能可接受，建议优化")
        print(f"      - 检查是否有资源瓶颈")
        print(f"      - 考虑增加缓存时间")
    else:
        print(f"   ❌ 性能较差，需要优化")
        print(f"      - 检查组件是否正常预热")
        print(f"      - 分析性能瓶颈")
        print(f"      - 考虑硬件升级")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    analyze_long_term_performance()
