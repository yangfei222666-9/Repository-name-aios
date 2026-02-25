#!/usr/bin/env python3
"""
AIOS 记忆盲区分析 v1.0
检测知识缺失、提供修复建议、超阈值自动提醒

用法:
  python -m aios.scripts.memory_gaps                    # 分析过去7天
  python -m aios.scripts.memory_gaps --days 3           # 自定义天数
  python -m aios.scripts.memory_gaps --format telegram  # 精简版
  python -m aios.scripts.memory_gaps --save             # 保存报告
"""

import json, sys, time, argparse
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, VALID_LAYERS
from core.config import get_path

WORKSPACE = Path.home() / ".openclaw" / "workspace"
MEMORY_DIR = WORKSPACE / "memory"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
SUGGESTIONS_LOG = (
    Path(__file__).resolve().parent.parent / "events" / "gap_suggestions.jsonl"
)

# 阈值
ALERT_THRESHOLD = 3  # 盲区数 >= 3 时触发提醒
REPEAT_THRESHOLD = 2  # 同一知识点 miss >= 2 次视为高频盲区


def _payload(e: dict) -> dict:
    return e.get("payload", e.get("data", {}))


def _event_name(e: dict) -> str:
    return e.get("event", _payload(e).get("_v1_type", e.get("type", "?")))


def _extract_topic(e: dict) -> str:
    """从 MEM 事件中提取知识主题"""
    p = _payload(e)
    # 尝试多种字段
    topic = (
        p.get("query")
        or p.get("topic")
        or p.get("key")
        or p.get("_v1_summary")
        or p.get("search_term")
        or ""
    )
    if not topic:
        # 从事件名推断
        name = _event_name(e)
        if "miss" in name:
            topic = name.replace("memory_miss_", "").replace("_miss", "")
    return str(topic).strip()[:100]


def _extract_context(e: dict) -> str:
    """提取事件上下文（用于修复建议）"""
    p = _payload(e)
    ctx = p.get("context") or p.get("source") or p.get("_v1_source") or ""
    return str(ctx).strip()[:200]


def _log_suggestions(suggestions: list):
    """落盘当前建议，供后续命中率计算"""
    if not suggestions:
        return
    SUGGESTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with SUGGESTIONS_LOG.open("a", encoding="utf-8") as f:
        for s in suggestions:
            entry = {
                "ts": ts,
                "epoch": int(now),
                "topic": s["topic"],
                "priority": s["priority"],
                "action": s["action"],
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _compute_hit_rate(current_gaps: Counter) -> dict:
    """
    计算修复命中率：之前建议过的主题，当前 miss 是否下降。
    返回 {total_suggested, fixed, still_open, hit_rate_pct}
    """
    if not SUGGESTIONS_LOG.exists():
        return {"total_suggested": 0, "fixed": 0, "still_open": 0, "hit_rate_pct": None}

    # 加载历史建议（去重，只看 7 天前的，给修复留时间）
    cutoff = time.time() - 7 * 86400
    past_topics = set()
    try:
        for line in SUGGESTIONS_LOG.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("epoch", 0) < cutoff:
                past_topics.add(entry.get("topic", ""))
    except:
        return {"total_suggested": 0, "fixed": 0, "still_open": 0, "hit_rate_pct": None}

    if not past_topics:
        return {"total_suggested": 0, "fixed": 0, "still_open": 0, "hit_rate_pct": None}

    # 对比：之前建议的主题，现在还在 miss 吗？
    fixed = 0
    still_open = 0
    for topic in past_topics:
        if topic in current_gaps and current_gaps[topic] > 0:
            still_open += 1
        else:
            fixed += 1

    total = len(past_topics)
    rate = round(fixed / total * 100, 1) if total > 0 else 0

    return {
        "total_suggested": total,
        "fixed": fixed,
        "still_open": still_open,
        "hit_rate_pct": rate,
    }


def scan_memory_files() -> dict:
    """扫描现有记忆文件，返回知识覆盖概况"""
    info = {
        "memory_md_exists": (WORKSPACE / "MEMORY.md").exists(),
        "memory_md_size": 0,
        "daily_files": [],
        "total_daily_size": 0,
        "lessons_exists": (MEMORY_DIR / "lessons.json").exists(),
        "corrections_exists": (MEMORY_DIR / "corrections.json").exists(),
    }

    if info["memory_md_exists"]:
        info["memory_md_size"] = (WORKSPACE / "MEMORY.md").stat().st_size

    if MEMORY_DIR.exists():
        for f in sorted(MEMORY_DIR.glob("202*.md")):
            size = f.stat().st_size
            info["daily_files"].append({"name": f.name, "size": size})
            info["total_daily_size"] += size

    return info


def analyze_gaps(days: int = 7) -> dict:
    """分析记忆盲区"""
    events = load_events(days, layer="MEM")

    # 分类 MEM 事件
    reads = []
    writes = []
    misses = []

    for e in events:
        name = _event_name(e)
        if any(k in name for k in ("miss", "not_found", "gap")):
            misses.append(e)
        elif any(
            k in name for k in ("recall", "match", "confirm", "load", "search", "read")
        ):
            reads.append(e)
        elif any(
            k in name for k in ("store", "correction", "lesson", "write", "update")
        ):
            writes.append(e)

    # 提取盲区主题
    gap_topics = Counter()
    gap_details = defaultdict(list)
    for e in misses:
        topic = _extract_topic(e)
        if topic:
            gap_topics[topic] += 1
            gap_details[topic].append(
                {
                    "ts": e.get("ts", "?"),
                    "context": _extract_context(e),
                    "event": _event_name(e),
                }
            )

    # 高频盲区（同一主题 miss 多次）
    high_freq = {t: c for t, c in gap_topics.items() if c >= REPEAT_THRESHOLD}

    # 读写比分析
    read_count = len(reads)
    write_count = len(writes)
    miss_count = len(misses)
    ratio = read_count / max(write_count, 1)

    # 知识覆盖
    read_topics = Counter(_extract_topic(e) for e in reads if _extract_topic(e))
    write_topics = Counter(_extract_topic(e) for e in writes if _extract_topic(e))
    # 读了但从没写过的 = 潜在盲区
    read_only = set(read_topics.keys()) - set(write_topics.keys())

    # 修复建议
    suggestions = []
    for topic, count in sorted(gap_topics.items(), key=lambda x: -x[1]):
        if not topic:
            continue
        details = gap_details[topic]
        contexts = [d["context"] for d in details if d["context"]]
        ctx_str = f"（来源: {contexts[0]}）" if contexts else ""
        if count >= REPEAT_THRESHOLD:
            suggestions.append(
                {
                    "priority": "高",
                    "topic": topic,
                    "reason": f"重复 miss {count} 次{ctx_str}",
                    "action": f"将「{topic}」相关知识补录到 MEMORY.md 或 lessons.json",
                }
            )
        else:
            suggestions.append(
                {
                    "priority": "中",
                    "topic": topic,
                    "reason": f"miss {count} 次{ctx_str}",
                    "action": f"下次遇到时主动记录「{topic}」",
                }
            )

    # 读多写少的潜在盲区
    for topic in sorted(read_only):
        if topic and read_topics[topic] >= 3:
            suggestions.append(
                {
                    "priority": "低",
                    "topic": topic,
                    "reason": f"读取 {read_topics[topic]} 次但从未写入",
                    "action": f"考虑将「{topic}」的常用知识固化到记忆文件",
                }
            )

    # 是否需要告警
    needs_alert = miss_count >= ALERT_THRESHOLD or len(high_freq) > 0

    # ── 修复命中率追踪 ──
    hit_rate = _compute_hit_rate(gap_topics)

    # 落盘当前建议（供后续命中率计算）
    _log_suggestions(suggestions)

    return {
        "days": days,
        "read_count": read_count,
        "write_count": write_count,
        "miss_count": miss_count,
        "ratio": round(ratio, 1),
        "gap_topics": dict(gap_topics),
        "high_freq_gaps": high_freq,
        "read_only_topics": sorted(read_only),
        "suggestions": suggestions,
        "needs_alert": needs_alert,
        "memory_info": scan_memory_files(),
        "hit_rate": hit_rate,
    }


def format_report(result: dict, compact: bool = False) -> str:
    now = time.strftime("%Y-%m-%d %H:%M")

    if compact:
        lines = [
            f"🧠 记忆盲区分析 | {now}",
            f"窗口: {result['days']}天",
            f"读{result['read_count']} 写{result['write_count']} 盲区{result['miss_count']} (读写比{result['ratio']}:1)",
        ]

        if result["high_freq_gaps"]:
            lines.append("")
            lines.append("⚠️ 高频盲区:")
            for topic, count in sorted(
                result["high_freq_gaps"].items(), key=lambda x: -x[1]
            ):
                lines.append(f"  🔴 {topic} ({count}次)")

        if result["suggestions"]:
            lines.append("")
            lines.append("📋 修复建议:")
            for s in result["suggestions"][:5]:
                icon = (
                    "🔴"
                    if s["priority"] == "高"
                    else "🟡" if s["priority"] == "中" else "🔵"
                )
                lines.append(f"  {icon} {s['action']}")

        if not result["gap_topics"]:
            lines.append("\n✅ 无记忆盲区")

        # 命中率
        hr = result.get("hit_rate", {})
        if hr.get("total_suggested", 0) > 0:
            lines.append(
                f"\n📈 修复命中率: {hr['hit_rate_pct']}% ({hr['fixed']}修复/{hr['total_suggested']}建议, {hr['still_open']}未修)"
            )

        return "\n".join(lines)

    # 完整 Markdown 版
    lines = [
        f"# 🧠 AIOS 记忆盲区分析报告",
        f"生成时间: {now} | 窗口: {result['days']}天",
        "",
        "## 1. 记忆概况",
        "",
        f"| 指标 | 值 |",
        f"| :--- | ---: |",
        f"| 知识提取 (Read) | {result['read_count']} |",
        f"| 知识固化 (Write) | {result['write_count']} |",
        f"| 知识盲区 (Miss) | {result['miss_count']} |",
        f"| 读写比 | {result['ratio']}:1 |",
    ]

    mi = result["memory_info"]
    lines.extend(
        [
            "",
            "## 2. 记忆文件状态",
            "",
            f"- MEMORY.md: {'✅' if mi['memory_md_exists'] else '❌'} ({mi['memory_md_size']} bytes)",
            f"- 日志文件: {len(mi['daily_files'])} 个 ({mi['total_daily_size']} bytes)",
            f"- lessons.json: {'✅' if mi['lessons_exists'] else '❌'}",
            f"- corrections.json: {'✅' if mi['corrections_exists'] else '❌'}",
        ]
    )

    if result["gap_topics"]:
        lines.extend(
            [
                "",
                "## 3. 盲区详情",
                "",
                "| 主题 | 次数 | 优先级 |",
                "| :--- | ---: | :--- |",
            ]
        )
        for topic, count in sorted(result["gap_topics"].items(), key=lambda x: -x[1]):
            pri = "🔴 高" if count >= REPEAT_THRESHOLD else "🟡 中"
            lines.append(f"| {topic} | {count} | {pri} |")

    if result["read_only_topics"]:
        lines.extend(
            [
                "",
                "## 4. 潜在盲区（读多写少）",
                "",
            ]
        )
        for t in result["read_only_topics"][:10]:
            lines.append(f"- {t}")

    if result["suggestions"]:
        lines.extend(
            [
                "",
                "## 5. 修复建议",
                "",
            ]
        )
        for s in result["suggestions"]:
            icon = (
                "🔴"
                if s["priority"] == "高"
                else "🟡" if s["priority"] == "中" else "🔵"
            )
            lines.append(f"- {icon} [{s['priority']}] {s['action']}")
            lines.append(f"  原因: {s['reason']}")

    if not result["gap_topics"] and not result["read_only_topics"]:
        lines.extend(
            ["", "✅ 过去 {} 天无记忆盲区，知识覆盖良好".format(result["days"])]
        )

    # 修复命中率
    hr = result.get("hit_rate", {})
    if hr.get("total_suggested", 0) > 0:
        lines.extend(
            [
                "",
                "## 6. 修复命中率",
                "",
                f"| 指标 | 值 |",
                f"| :--- | ---: |",
                f"| 历史建议数 | {hr['total_suggested']} |",
                f"| 已修复 | {hr['fixed']} |",
                f"| 未修复 | {hr['still_open']} |",
                f"| 命中率 | {hr['hit_rate_pct']}% |",
            ]
        )

    lines.extend(
        [
            "",
            "---",
            f"*Generated by AIOS Memory Gaps v1.0 | {now}*",
        ]
    )

    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="AIOS 记忆盲区分析")
    p.add_argument("--days", type=int, default=7, help="分析窗口（天）")
    p.add_argument("--format", choices=["markdown", "telegram"], default="markdown")
    p.add_argument("--save", action="store_true", help="保存报告")
    args = p.parse_args()

    result = analyze_gaps(args.days)
    report = format_report(result, compact=(args.format == "telegram"))
    print(report)

    if result["needs_alert"]:
        print("\n⚠️ 盲区超阈值，建议尽快修复！")

    if args.save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out = REPORTS_DIR / f"memory_gaps_{ts}.md"
        out.write_text(report, encoding="utf-8")
        print(f"\n💾 已保存: {out}")


if __name__ == "__main__":
    main()
