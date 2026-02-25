# aios/learning/analyze_aram.py - ARAM 专项分析
"""
从 events.jsonl 中提取 aram.matcher 相关事件，产出 ARAM 专项报告。
"""

import json, time, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events
from core.config import get_int, get_float

CORRECTION_THRESHOLD = get_int("analysis.correction_threshold", 3)


def aram_metrics(days: int = 7) -> dict:
    events = load_events(days)
    matches = [
        e
        for e in events
        if e.get("source") == "aram.matcher" and e.get("type") == "match"
    ]
    corrections = [
        e
        for e in events
        if e.get("source") == "aram.matcher" and e.get("type") == "correction"
    ]

    total = len(matches) + len(corrections)
    correction_rate = len(corrections) / total if total > 0 else 0

    # match_type 分布
    type_dist = Counter((e.get("data") or {}).get("match_type", "?") for e in matches)

    # 平均 score
    scores = [
        (e.get("data") or {}).get("score", 0)
        for e in matches
        if (e.get("data") or {}).get("score")
    ]
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "period_days": days,
        "total_matches": len(matches),
        "total_corrections": len(corrections),
        "correction_rate": round(correction_rate, 3),
        "avg_score": round(avg_score, 3),
        "match_type_distribution": dict(type_dist),
    }


def aram_top_issues(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [
        e
        for e in events
        if e.get("source") == "aram.matcher" and e.get("type") == "correction"
    ]

    # 最常被纠正的输入
    corrected_inputs = Counter(
        (e.get("data") or {}).get("input", "?") for e in corrections
    )

    # 纠正流向：input → correct_target
    flows = defaultdict(Counter)
    for c in corrections:
        data = c.get("data", {})
        inp = data.get("input", "")
        target = data.get("correct_target", "")
        if inp and target:
            flows[inp][target] += 1

    top_flows = {}
    for inp, targets in flows.items():
        top_target, count = targets.most_common(1)[0]
        top_flows[inp] = {"target": top_target, "count": count}

    return {
        "top_corrected": dict(corrected_inputs.most_common(10)),
        "correction_flows": top_flows,
    }


def aram_alias_suggestions(days: int = 7) -> list:
    """基于纠正流向生成 alias 建议"""
    issues = aram_top_issues(days)
    suggestions = []

    for inp, flow in issues["correction_flows"].items():
        if flow["count"] >= CORRECTION_THRESHOLD:
            suggestions.append(
                {
                    "input": inp,
                    "suggested": flow["target"],
                    "reason": f"corrected_{flow['count']}_times",
                    "confidence": (
                        1.0 if flow["count"] >= 5 else round(flow["count"] / 5, 2)
                    ),
                }
            )

    return suggestions


def report(days: int = 7) -> str:
    m = aram_metrics(days)
    issues = aram_top_issues(days)
    sug = aram_alias_suggestions(days)

    lines = [
        f"# ARAM Analysis ({days}d)",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
        "## Metrics",
        f"- matches: {m['total_matches']}",
        f"- corrections: {m['total_corrections']}",
        f"- correction_rate: {m['correction_rate']:.1%}",
        f"- avg_score: {m['avg_score']:.2f}",
    ]

    if m["match_type_distribution"]:
        lines.append("- match_types:")
        for t, c in m["match_type_distribution"].items():
            lines.append(f"  - {t}: {c}")

    if issues["top_corrected"]:
        lines.append("\n## Top Corrected")
        for inp, cnt in issues["top_corrected"].items():
            flow = issues["correction_flows"].get(inp, {})
            target = flow.get("target", "?")
            lines.append(f'- "{inp}" x{cnt} → {target}')

    if sug:
        lines.append("\n## Alias Suggestions")
        for s in sug:
            lines.append(
                f"- \"{s['input']}\" → \"{s['suggested']}\" (confidence: {s['confidence']})"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(report(days))
