# aios/scripts/replay.py - 回放模式（科学迭代）
"""
从 events.jsonl 抽一段时间，重跑 analyze，对比新旧 suggestions。
用途：调阈值/改策略后验证效果。
"""

import json, time, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events

AIOS_ROOT = Path(__file__).resolve().parent.parent


def replay(start_ts: int, end_ts: int, days: int = 30) -> dict:
    """抽取 [start_ts, end_ts] 的事件，写入临时文件，重跑 analyze"""
    all_events = load_events(days)
    filtered = [e for e in all_events if start_ts <= e.get("ts", 0) <= end_ts]

    if not filtered:
        return {"error": "no events in range", "count": 0}

    # 写临时 events 文件
    tmp_dir = Path(tempfile.mkdtemp(prefix="aios_replay_"))
    tmp_events = tmp_dir / "events.jsonl"
    with tmp_events.open("w", encoding="utf-8") as f:
        for e in filtered:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # monkey-patch events path
    import core.engine as engine

    original_path = engine._events_path

    engine._events_path = lambda: tmp_events

    try:
        from learning.analyze import generate_full_report

        report = generate_full_report(days=days)
    finally:
        engine._events_path = original_path
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return {
        "events_count": len(filtered),
        "time_range": {
            "start": time.strftime("%Y-%m-%d %H:%M", time.localtime(start_ts)),
            "end": time.strftime("%Y-%m-%d %H:%M", time.localtime(end_ts)),
        },
        "report": report,
    }


def compare(report_a: dict, report_b: dict) -> dict:
    """对比两份报告的关键指标"""
    ma = report_a.get("report", report_a).get("metrics", {})
    mb = report_b.get("report", report_b).get("metrics", {})

    diff = {}
    for key in ("match_correction_rate", "tool_success_rate", "low_score_ratio"):
        va = ma.get(key, 0)
        vb = mb.get(key, 0)
        diff[key] = {"before": va, "after": vb, "delta": round(vb - va, 4)}

    sa = report_a.get("report", report_a).get("alias_suggestions", [])
    sb = report_b.get("report", report_b).get("alias_suggestions", [])
    ta = report_a.get("report", report_a).get("tool_suggestions", [])
    tb = report_b.get("report", report_b).get("tool_suggestions", [])

    diff["alias_suggestions"] = {"before": len(sa), "after": len(sb)}
    diff["tool_suggestions"] = {"before": len(ta), "after": len(tb)}

    return diff


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: replay.py <start_hours_ago> <end_hours_ago>")
        print("  e.g.: replay.py 48 0  (replay last 48h)")
        sys.exit(1)

    now = int(time.time())
    start_ago = int(sys.argv[1])
    end_ago = int(sys.argv[2])
    start_ts = now - start_ago * 3600
    end_ts = now - end_ago * 3600

    result = replay(start_ts, end_ts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
