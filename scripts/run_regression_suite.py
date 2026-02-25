# aios/scripts/run_regression_suite.py - 回归测试套件
"""
验证 AIOS 所有核心模块正常工作。
python scripts/run_regression_suite.py
"""

import sys, json, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PASS = 0
FAIL = 0
RESULTS = []


def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        RESULTS.append(("PASS", name))
        print(f"  ✓ {name}")
    except Exception as e:
        FAIL += 1
        RESULTS.append(("FAIL", name, str(e)))
        print(f"  ✗ {name}: {e}")


# === core ===


def test_config():
    from core.config import load, get, get_path, get_float, get_bool, get_int

    cfg = load()
    assert len(cfg) > 0, "config empty"
    assert get("config.name") == "AIOS"
    assert get_path("paths.events") is not None
    assert get_float("policy.alias_min_confidence") == 0.80
    assert get_bool("policy.alias_no_overwrite") is True
    assert get_int("analysis.correction_threshold") == 3


def test_engine_log_and_load():
    from core.engine import (
        log_event,
        load_events,
        log_tool_event,
        append_jsonl,
        count_by_type,
    )

    ev = log_event("test", "regression", "test event", {"key": "value"})
    assert ev["type"] == "test"
    assert ev["ts"] > 0

    tev = log_tool_event("test_tool", True, 42)
    assert tev["data"]["name"] == "test_tool"
    assert tev["data"]["ms"] == 42

    events = load_events(days=1, event_type="test")
    assert len(events) >= 1

    counts = count_by_type(days=1)
    assert "test" in counts


def test_policies():
    from core.policies import apply_alias_suggestion

    alias_map = {}
    item = {"input": "卡特", "suggested": "卡莎", "confidence": 0.9}
    applied, why = apply_alias_suggestion(alias_map, item, 0.8, True)
    assert applied is True
    assert why == "applied_append_new_key"
    assert alias_map["卡特"] == "卡莎"

    # no overwrite
    item2 = {"input": "卡特", "suggested": "卡特琳娜", "confidence": 0.95}
    applied2, why2 = apply_alias_suggestion(alias_map, item2, 0.8, True)
    assert applied2 is False
    assert why2 == "skip_existing_key_no_overwrite"

    # low confidence
    alias_map2 = {}
    item3 = {"input": "x", "suggested": "y", "confidence": 0.3}
    applied3, why3 = apply_alias_suggestion(alias_map2, item3, 0.8, True)
    assert applied3 is False
    assert why3 == "skip_low_confidence"


# === learning ===


def test_analyze_metrics():
    from learning.analyze import compute_metrics

    m = compute_metrics(days=1)
    assert "counts" in m
    assert "quality" in m
    assert "reliability" in m
    assert "performance" in m


def test_analyze_suggestions():
    from learning.analyze import (
        compute_alias_suggestions,
        compute_tool_suggestions,
        compute_threshold_warnings,
    )

    # 这些不应该崩
    compute_alias_suggestions(days=1)
    compute_tool_suggestions(days=1)
    compute_threshold_warnings(days=1)


def test_analyze_full_report():
    from learning.analyze import generate_full_report

    r = generate_full_report(days=1)
    assert "ts" in r
    assert "window" in r
    assert "version" in r
    assert "alias_suggestions" in r
    assert "tool_suggestions" in r


def test_analyze_daily_report():
    from learning.analyze import generate_daily_report

    text = generate_daily_report(days=1)
    assert "AIOS Daily Report" in text
    assert "Evolution Score" in text


def test_baseline_snapshot():
    from learning.baseline import snapshot, load_history, evolution_score

    r = snapshot(days=1)
    assert "correction_rate" in r
    assert "tool_success_rate" in r
    assert "tool_p95_ms" in r

    h = load_history(limit=5)
    assert len(h) >= 1

    evo = evolution_score()
    assert "score" in evo
    assert "grade" in evo
    assert evo["grade"] in ("healthy", "ok", "degraded", "critical", "N/A")


def test_tickets():
    from learning.tickets import ingest, load_tickets, summary

    result = ingest(
        [
            {
                "level": "L2",
                "name": "test_tool",
                "action": "monitor",
                "reason": "regression_test",
                "confidence": 0.5,
                "evidence": {},
            }
        ]
    )
    assert result["created"] >= 0
    s = summary()
    assert isinstance(s, str)


def test_apply():
    from learning.apply import load_suggestions, load_learned

    # 不崩就行
    load_suggestions()
    load_learned()


# === plugins ===


def test_aram_matcher():
    from plugins.aram.data_adapter import load_champions, champion_count

    count = champion_count()
    # 可能没数据文件，跳过
    if count == 0:
        return

    from plugins.aram.matcher import match

    results = match("亚索")
    assert len(results) >= 1
    assert results[0]["score"] > 0


def test_aram_rules():
    from plugins.aram.rules import BUILTIN_ALIASES

    assert "卡特" in BUILTIN_ALIASES
    assert "盲僧" in BUILTIN_ALIASES
    assert BUILTIN_ALIASES["vn"] == "67"


def test_aram_data_adapter():
    from plugins.aram.data_adapter import load_aliases, save_aliases

    # round-trip
    aliases = load_aliases()
    assert isinstance(aliases, dict)


# === gateway collector ===


def test_gateway_collector():
    from plugins.gateway.collector import record_tool, daily_summary

    record_tool("exec", True, 100)
    s = daily_summary()
    assert "tools" in s
    assert "total_calls" in s


# === replay ===


def test_replay():
    from scripts.replay import replay

    now = int(time.time())
    r = replay(now - 3600, now, days=1)
    assert "events_count" in r


def _getv(d: dict, path: str, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _load_last_n_jsonl(path: Path, n: int) -> list:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-n:]:
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def run_metrics_regression() -> tuple:
    """对比最近两次 baseline，检查是否退化"""
    from core.config import get_path

    hist = get_path("paths.metrics_history")
    if not hist:
        hist = Path(__file__).resolve().parent.parent / "learning" / "baseline.jsonl"

    last2 = _load_last_n_jsonl(hist, 2)
    if len(last2) < 2:
        print("  ⚠ not enough baseline history (need >=2), skipping metrics regression")
        return (0, 0)

    prev, curr = last2[-2], last2[-1]
    checks = [
        ("correction_rate", "correction_rate", "down"),
        ("tool_success_rate", "tool_success_rate", "up"),
        ("http_502_rate", "http_502_rate", "down"),
        ("http_404_rate", "http_404_rate", "down"),
    ]

    ok = 0
    total = 0
    print(f"  comparing: {prev.get('ts', '?')} → {curr.get('ts', '?')}")

    for name, path, direction in checks:
        a = _getv(prev, path, 0)
        b = _getv(curr, path, 0)
        total += 1

        if direction == "down":
            passed = b <= a
            arrow = "↓" if b < a else "→"
        else:
            passed = b >= a
            arrow = "↑" if b > a else "→"

        if passed:
            ok += 1
            RESULTS.append(("PASS", f"metrics:{name}"))
            print(f"  ✓ {name}: {a} → {b} {arrow}")
        else:
            RESULTS.append(
                ("FAIL", f"metrics:{name}", f"{a} → {b} (expected {direction})")
            )
            print(f"  ✗ {name}: {a} → {b} {arrow} (expected {direction})")

    return (ok, total)


# === run ===

if __name__ == "__main__":
    print("AIOS Regression Suite\n")

    print("[core]")
    test("config", test_config)
    test("engine_log_and_load", test_engine_log_and_load)
    test("policies", test_policies)

    print("\n[learning]")
    test("analyze_metrics", test_analyze_metrics)
    test("analyze_suggestions", test_analyze_suggestions)
    test("analyze_full_report", test_analyze_full_report)
    test("analyze_daily_report", test_analyze_daily_report)
    test("baseline_snapshot", test_baseline_snapshot)
    test("tickets", test_tickets)
    test("apply", test_apply)

    print("\n[plugins]")
    test("aram_matcher", test_aram_matcher)
    test("aram_rules", test_aram_rules)
    test("aram_data_adapter", test_aram_data_adapter)
    test("gateway_collector", test_gateway_collector)

    print("\n[scripts]")
    test("replay", test_replay)

    # === metrics regression (baseline compare) ===
    print("\n[metrics regression]")
    metrics_ok, metrics_total = run_metrics_regression()
    PASS += metrics_ok
    FAIL += metrics_total - metrics_ok

    print(f"\n{'='*40}")
    print(f"Results: {PASS} passed, {FAIL} failed, {PASS+FAIL} total")

    if FAIL > 0:
        print("\nFailed tests:")
        for r in RESULTS:
            if r[0] == "FAIL":
                print(f"  ✗ {r[1]}: {r[2]}")
        sys.exit(1)
    else:
        print("All green ✓")
        sys.exit(0)
