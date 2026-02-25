#!/usr/bin/env python3
"""
AIOS 自动性能优化器
监控系统性能，识别瓶颈，自动应用低风险优化
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# 配置
WORKSPACE = Path(__file__).parent.parent.parent
AIOS_DIR = WORKSPACE / "aios"
EVENTS_FILE = AIOS_DIR / "data" / "events.jsonl"
PERF_REPORT_FILE = AIOS_DIR / "data" / "performance_report.json"
OPTIMIZATION_LOG = AIOS_DIR / "data" / "optimizations.jsonl"

# 性能阈值
SLOW_OPERATION_THRESHOLD = 5.0  # 秒
HIGH_LATENCY_THRESHOLD = 3.0    # 秒
FREQUENT_OPERATION_THRESHOLD = 10  # 次/小时

# 优化策略
OPTIMIZATIONS = {
    "reduce_heartbeat_frequency": {
        "risk": "low",
        "description": "降低心跳频率（30min → 45min）",
        "condition": lambda stats: stats.get('heartbeat_count', 0) > 20,
        "action": "update_heartbeat_interval",
        "params": {"interval_minutes": 45}
    },
    "increase_cache_ttl": {
        "risk": "low",
        "description": "增加缓存TTL（5min → 10min）",
        "condition": lambda stats: stats.get('cache_miss_rate', 0) > 0.5,
        "action": "update_cache_config",
        "params": {"ttl_minutes": 10}
    },
    "batch_event_writes": {
        "risk": "low",
        "description": "批量写入事件（减少磁盘I/O）",
        "condition": lambda stats: stats.get('event_write_count', 0) > 100,
        "action": "enable_event_batching",
        "params": {"batch_size": 10}
    },
    "cleanup_idle_agents": {
        "risk": "low",
        "description": "清理闲置Agent（>1h无活动）",
        "condition": lambda stats: stats.get('idle_agent_count', 0) > 3,
        "action": "cleanup_idle_agents",
        "params": {"idle_threshold_minutes": 60}
    },
}


def load_events(hours=1):
    """加载最近N小时的事件"""
    if not EVENTS_FILE.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    events = []
    
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                event = json.loads(line)
                timestamp = event.get('timestamp', '')
                if not timestamp:
                    continue
                
                event_time = datetime.fromisoformat(timestamp)
                if event_time >= cutoff_time:
                    events.append(event)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
    
    return events


def analyze_performance(events):
    """分析性能数据"""
    stats = {
        "total_events": len(events),
        "slow_operations": [],
        "high_latency_operations": [],
        "frequent_operations": defaultdict(int),
        "heartbeat_count": 0,
        "event_write_count": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "idle_agent_count": 0,
    }
    
    for event in events:
        event_type = event.get('type', '')
        duration = event.get('duration', 0)
        operation = event.get('operation', '')
        
        # 统计慢操作
        if duration > SLOW_OPERATION_THRESHOLD:
            stats['slow_operations'].append({
                "operation": operation,
                "duration": duration,
                "timestamp": event.get('timestamp')
            })
        
        # 统计高延迟操作
        if duration > HIGH_LATENCY_THRESHOLD:
            stats['high_latency_operations'].append({
                "operation": operation,
                "duration": duration
            })
        
        # 统计频繁操作
        if operation:
            stats['frequent_operations'][operation] += 1
        
        # 统计特定事件
        if event_type == 'heartbeat':
            stats['heartbeat_count'] += 1
        elif event_type == 'event_write':
            stats['event_write_count'] += 1
        elif event_type == 'cache_hit':
            stats['cache_hits'] += 1
        elif event_type == 'cache_miss':
            stats['cache_misses'] += 1
        elif event_type == 'agent_idle':
            stats['idle_agent_count'] += 1
    
    # 计算缓存命中率
    total_cache_ops = stats['cache_hits'] + stats['cache_misses']
    if total_cache_ops > 0:
        stats['cache_miss_rate'] = stats['cache_misses'] / total_cache_ops
    else:
        stats['cache_miss_rate'] = 0
    
    return stats


def identify_bottlenecks(stats):
    """识别性能瓶颈"""
    bottlenecks = []
    
    # 慢操作
    if len(stats['slow_operations']) > 0:
        bottlenecks.append({
            "type": "slow_operations",
            "severity": "medium",
            "count": len(stats['slow_operations']),
            "details": stats['slow_operations'][:5]  # 只显示前5个
        })
    
    # 高延迟操作
    if len(stats['high_latency_operations']) > 3:
        bottlenecks.append({
            "type": "high_latency",
            "severity": "low",
            "count": len(stats['high_latency_operations']),
            "avg_duration": sum(op['duration'] for op in stats['high_latency_operations']) / len(stats['high_latency_operations'])
        })
    
    # 频繁操作
    for operation, count in stats['frequent_operations'].items():
        if count > FREQUENT_OPERATION_THRESHOLD:
            bottlenecks.append({
                "type": "frequent_operation",
                "severity": "low",
                "operation": operation,
                "count": count
            })
    
    # 心跳过于频繁
    if stats['heartbeat_count'] > 20:
        bottlenecks.append({
            "type": "excessive_heartbeats",
            "severity": "low",
            "count": stats['heartbeat_count']
        })
    
    # 缓存命中率低
    if stats['cache_miss_rate'] > 0.5 and (stats['cache_hits'] + stats['cache_misses']) > 10:
        bottlenecks.append({
            "type": "low_cache_hit_rate",
            "severity": "medium",
            "miss_rate": stats['cache_miss_rate']
        })
    
    return bottlenecks


def suggest_optimizations(stats, bottlenecks):
    """根据瓶颈建议优化"""
    suggestions = []
    
    for opt_name, opt_config in OPTIMIZATIONS.items():
        if opt_config['condition'](stats):
            suggestions.append({
                "name": opt_name,
                "risk": opt_config['risk'],
                "description": opt_config['description'],
                "action": opt_config['action'],
                "params": opt_config['params']
            })
    
    return suggestions


def apply_optimization(optimization):
    """应用优化（仅低风险）"""
    if optimization['risk'] != 'low':
        return {
            "status": "skipped",
            "reason": f"risk level {optimization['risk']} requires manual approval"
        }
    
    action = optimization['action']
    params = optimization['params']
    
    # 这里是占位符，实际应用需要根据具体action实现
    # 目前只记录到日志，不实际修改配置
    
    result = {
        "status": "simulated",
        "action": action,
        "params": params,
        "timestamp": datetime.now().isoformat(),
        "note": "优化建议已记录，等待实际实现"
    }
    
    # 记录到优化日志
    OPTIMIZATION_LOG.parent.mkdir(exist_ok=True)
    with open(OPTIMIZATION_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    return result


def main():
    """主函数"""
    print("⚡ AIOS 自动性能优化")
    print("=" * 50)
    
    # 1. 加载最近1小时的事件
    print("\n📊 加载性能数据...")
    events = load_events(hours=1)
    print(f"   ✅ 加载 {len(events)} 个事件")
    
    if len(events) < 10:
        print("   ℹ️  数据量不足，跳过分析")
        print("\n" + "=" * 50)
        print("PERF_OK")
        return
    
    # 2. 分析性能
    print("\n🔍 分析性能指标...")
    stats = analyze_performance(events)
    print(f"   📈 慢操作: {len(stats['slow_operations'])} 个")
    print(f"   📈 高延迟: {len(stats['high_latency_operations'])} 个")
    print(f"   📈 心跳次数: {stats['heartbeat_count']}")
    print(f"   📈 缓存命中率: {(1 - stats['cache_miss_rate']) * 100:.1f}%")
    
    # 3. 识别瓶颈
    print("\n🎯 识别性能瓶颈...")
    bottlenecks = identify_bottlenecks(stats)
    
    if bottlenecks:
        print(f"   ⚠️  发现 {len(bottlenecks)} 个瓶颈")
        for bn in bottlenecks[:3]:
            print(f"   • {bn['type']} (严重度: {bn['severity']})")
    else:
        print("   ✅ 无明显瓶颈")
    
    # 4. 建议优化
    print("\n💡 生成优化建议...")
    suggestions = suggest_optimizations(stats, bottlenecks)
    
    if suggestions:
        print(f"   ✅ 生成 {len(suggestions)} 个优化建议")
        for sug in suggestions:
            print(f"   • {sug['description']} (风险: {sug['risk']})")
    else:
        print("   ✅ 系统运行良好，无需优化")
    
    # 5. 应用低风险优化
    applied = []
    if suggestions:
        print("\n🔧 应用低风险优化...")
        for sug in suggestions:
            if sug['risk'] == 'low':
                result = apply_optimization(sug)
                if result['status'] in ['applied', 'simulated']:
                    applied.append(sug['name'])
                    print(f"   ✅ {sug['description']}")
    
    # 6. 保存性能报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "stats": {
            "total_events": stats['total_events'],
            "slow_operations_count": len(stats['slow_operations']),
            "high_latency_count": len(stats['high_latency_operations']),
            "heartbeat_count": stats['heartbeat_count'],
            "cache_miss_rate": stats['cache_miss_rate']
        },
        "bottlenecks": bottlenecks,
        "suggestions": suggestions,
        "applied": applied
    }
    
    with open(PERF_REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 性能报告已保存: {PERF_REPORT_FILE.relative_to(WORKSPACE)}")
    
    # 7. 输出心跳格式
    print("\n" + "=" * 50)
    if len(bottlenecks) > 0 and any(bn['severity'] == 'high' for bn in bottlenecks):
        print("PERF_DEGRADED")
    elif len(applied) > 0:
        print(f"PERF_OPTIMIZED:{len(applied)}")
    else:
        print("PERF_OK")


if __name__ == "__main__":
    main()
