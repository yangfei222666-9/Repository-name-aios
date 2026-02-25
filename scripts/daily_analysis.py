"""
AIOS v0.5 事件日志自动分析脚本
按天汇总触发次数、修复成功率、平均评分、降级时长

使用方法：
python -X utf8 aios/scripts/daily_analysis.py [--days 7] [--format telegram]
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))


def load_events(events_file: Path, since_days: int = 7):
    """加载最近 N 天的事件"""
    if not events_file.exists():
        return []
    
    cutoff_time = int((datetime.now() - timedelta(days=since_days)).timestamp() * 1000)
    
    events = []
    with open(events_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line.strip())
                if event.get("timestamp", 0) >= cutoff_time:
                    events.append(event)
            except:
                pass
    
    return events


def analyze_events(events):
    """分析事件"""
    # 按天分组
    daily_stats = defaultdict(lambda: {
        "date": None,
        "total_events": 0,
        "resource_alerts": 0,
        "scheduler_decisions": 0,
        "reactor_executions": 0,
        "reactor_success": 0,
        "reactor_failed": 0,
        "score_updates": [],
        "degraded_periods": [],
        "event_types": defaultdict(int)
    })
    
    # 降级状态追踪
    degraded_start = None
    
    for event in events:
        # 转换时间戳
        timestamp = event.get("timestamp", 0)
        date = datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        
        stats = daily_stats[date]
        stats["date"] = date
        stats["total_events"] += 1
        
        # 事件类型统计
        event_type = event.get("type", "unknown")
        stats["event_types"][event_type] += 1
        
        # 资源告警
        if event_type.startswith("resource."):
            stats["resource_alerts"] += 1
        
        # Scheduler 决策
        elif event_type == "scheduler.decision":
            stats["scheduler_decisions"] += 1
        
        # Reactor 执行
        elif event_type == "reactor.success":
            stats["reactor_executions"] += 1
            stats["reactor_success"] += 1
        elif event_type == "reactor.failed":
            stats["reactor_executions"] += 1
            stats["reactor_failed"] += 1
        
        # Score 更新
        elif event_type == "score.updated":
            score = event.get("payload", {}).get("score", 0)
            stats["score_updates"].append(score)
        
        # 降级检测
        elif event_type == "score.degraded":
            degraded_start = timestamp
        elif event_type == "score.recovered":
            if degraded_start:
                duration = (timestamp - degraded_start) / 1000  # 秒
                stats["degraded_periods"].append(duration)
                degraded_start = None
    
    return daily_stats


def format_report(daily_stats, format_type="markdown"):
    """格式化报告"""
    if format_type == "telegram":
        return format_telegram(daily_stats)
    else:
        return format_markdown(daily_stats)


def format_markdown(daily_stats):
    """Markdown 格式"""
    lines = []
    lines.append("# AIOS v0.5 每日分析报告")
    lines.append("")
    
    # 按日期排序
    sorted_dates = sorted(daily_stats.keys(), reverse=True)
    
    for date in sorted_dates:
        stats = daily_stats[date]
        
        lines.append(f"## {date}")
        lines.append("")
        
        # 基础统计
        lines.append(f"**总事件数:** {stats['total_events']}")
        lines.append(f"**资源告警:** {stats['resource_alerts']}")
        lines.append(f"**Scheduler 决策:** {stats['scheduler_decisions']}")
        lines.append("")
        
        # Reactor 统计
        if stats['reactor_executions'] > 0:
            success_rate = stats['reactor_success'] / stats['reactor_executions']
            lines.append(f"**Reactor 执行:** {stats['reactor_executions']} 次")
            lines.append(f"  - 成功: {stats['reactor_success']}")
            lines.append(f"  - 失败: {stats['reactor_failed']}")
            lines.append(f"  - 成功率: {success_rate:.1%}")
        else:
            lines.append(f"**Reactor 执行:** 0 次")
        lines.append("")
        
        # Score 统计
        if stats['score_updates']:
            avg_score = sum(stats['score_updates']) / len(stats['score_updates'])
            min_score = min(stats['score_updates'])
            max_score = max(stats['score_updates'])
            lines.append(f"**系统评分:**")
            lines.append(f"  - 平均: {avg_score:.3f}")
            lines.append(f"  - 最低: {min_score:.3f}")
            lines.append(f"  - 最高: {max_score:.3f}")
        else:
            lines.append(f"**系统评分:** 无数据")
        lines.append("")
        
        # 降级统计
        if stats['degraded_periods']:
            total_degraded = sum(stats['degraded_periods'])
            avg_degraded = total_degraded / len(stats['degraded_periods'])
            lines.append(f"**降级统计:**")
            lines.append(f"  - 次数: {len(stats['degraded_periods'])}")
            lines.append(f"  - 总时长: {total_degraded:.1f}s")
            lines.append(f"  - 平均时长: {avg_degraded:.1f}s")
        else:
            lines.append(f"**降级统计:** 无降级")
        lines.append("")
        
        # 高频事件类型（Top 5）
        top_events = sorted(stats['event_types'].items(), key=lambda x: x[1], reverse=True)[:5]
        if top_events:
            lines.append(f"**高频事件 (Top 5):**")
            for event_type, count in top_events:
                lines.append(f"  - {event_type}: {count}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    return "\n".join(lines)


def format_telegram(daily_stats):
    """Telegram 格式（简洁版）"""
    lines = []
    lines.append("📊 AIOS 每日分析")
    lines.append("")
    
    # 只显示最近 3 天
    sorted_dates = sorted(daily_stats.keys(), reverse=True)[:3]
    
    for date in sorted_dates:
        stats = daily_stats[date]
        
        lines.append(f"📅 {date}")
        lines.append(f"事件: {stats['total_events']} | 告警: {stats['resource_alerts']}")
        
        # Reactor
        if stats['reactor_executions'] > 0:
            success_rate = stats['reactor_success'] / stats['reactor_executions']
            lines.append(f"修复: {stats['reactor_executions']}次 ({success_rate:.0%}成功)")
        
        # Score
        if stats['score_updates']:
            avg_score = sum(stats['score_updates']) / len(stats['score_updates'])
            lines.append(f"评分: {avg_score:.3f}")
        
        # 降级
        if stats['degraded_periods']:
            lines.append(f"⚠️ 降级 {len(stats['degraded_periods'])}次")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS 事件日志分析")
    parser.add_argument("--days", type=int, default=7, help="分析最近 N 天（默认 7）")
    parser.add_argument("--format", choices=["markdown", "telegram"], default="markdown", help="输出格式")
    parser.add_argument("--save", action="store_true", help="保存到文件")
    
    args = parser.parse_args()
    
    # 加载事件
    events_file = AIOS_ROOT / "data" / "events.jsonl"
    
    if not events_file.exists():
        print("❌ 事件文件不存在")
        print(f"   路径: {events_file}")
        return
    
    print(f"📊 分析最近 {args.days} 天的事件...")
    events = load_events(events_file, args.days)
    
    if not events:
        print("❌ 没有找到事件数据")
        return
    
    print(f"✅ 加载了 {len(events)} 个事件")
    
    # 分析
    daily_stats = analyze_events(events)
    
    if not daily_stats:
        print("❌ 没有可分析的数据")
        return
    
    # 格式化报告
    report = format_report(daily_stats, args.format)
    
    # 输出
    print("")
    print(report)
    
    # 保存
    if args.save:
        output_file = AIOS_ROOT / "reports" / f"daily_analysis_{datetime.now().strftime('%Y%m%d')}.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n✅ 报告已保存: {output_file}")


if __name__ == "__main__":
    main()
