"""
Hexagram Timeline Visualizer - 卦象演化可视化

生成 Markdown 报告，展示：
1. 卦象时间线（最近 7 天）
2. 卦象转移频率（Top 10）
3. 系统演化路径
"""

from pathlib import Path
from datetime import datetime

try:
    from .hexagram_logger import get_hexagram_timeline, analyze_transitions, get_recent_hexagrams
except ImportError:
    from hexagram_logger import get_hexagram_timeline, analyze_transitions, get_recent_hexagrams

# 报告输出路径
REPORT_DIR = Path(__file__).parent.parent / "reports"


def generate_timeline_report(output_file: str = None):
    """
    生成卦象时间线报告
    
    Args:
        output_file: 输出文件路径（默认：reports/hexagram_timeline.md）
    """
    if output_file is None:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = REPORT_DIR / "hexagram_timeline.md"
    
    # 获取数据
    timeline = get_hexagram_timeline(days=7)
    transitions = analyze_transitions(min_count=1)
    recent = get_recent_hexagrams(limit=20)
    
    # 生成报告
    lines = []
    lines.append("# AIOS Hexagram Timeline Report")
    lines.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("\n---\n")
    
    # 1. 卦象时间线
    lines.append("## 📅 Hexagram Timeline (Last 7 Days)\n")
    if timeline:
        lines.append("```")
        for t in timeline:
            bar = "█" * (t["count"] // 2 + 1)  # 简单柱状图
            lines.append(f"{t['date']} | {t['hexagram']:6s} | {bar} ({t['count']}/{t['total']})")
        lines.append("```")
        
        # 演化路径
        path = " → ".join([t["hexagram"] for t in timeline])
        lines.append(f"\n**Evolution Path:** {path}\n")
    else:
        lines.append("*No data yet. System is collecting...*\n")
    
    # 2. 卦象转移频率
    lines.append("## 🔄 Hexagram Transitions (Top 10)\n")
    if transitions:
        lines.append("| From | To | Count |")
        lines.append("|------|-----|-------|")
        for trans in transitions[:10]:
            lines.append(f"| {trans['from']} | {trans['to']} | {trans['count']} |")
        lines.append("")
    else:
        lines.append("*No transitions recorded yet.*\n")
    
    # 3. 最近状态
    lines.append("## 🕐 Recent States (Last 20)\n")
    if recent:
        lines.append("```")
        for r in recent:
            timestamp = r["timestamp"][:19].replace("T", " ")
            lines.append(f"{timestamp} | {r['hexagram']:6s} | SR={r['success_rate']:.2%} | Latency={r['latency']:.1f}s")
        lines.append("```")
    else:
        lines.append("*No recent states.*\n")
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return output_file


def print_timeline_summary():
    """
    打印卦象时间线摘要（用于 Heartbeat）
    """
    timeline = get_hexagram_timeline(days=7)
    
    if not timeline:
        print("[HEXAGRAM] No timeline data yet")
        return
    
    # 最近 3 天的卦象
    recent_days = timeline[-3:]
    path = " → ".join([t["hexagram"] for t in recent_days])
    
    print(f"[HEXAGRAM] Recent path: {path}")
    
    # 当前卦象
    current = timeline[-1]
    print(f"[HEXAGRAM] Current: {current['hexagram']} ({current['count']}/{current['total']} today)")


if __name__ == "__main__":
    print("Generating Hexagram Timeline Report...")
    output = generate_timeline_report()
    print(f"✅ Report saved: {output}")
    
    print("\n" + "=" * 60)
    print_timeline_summary()
