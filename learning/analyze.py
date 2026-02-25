# aios/learning/analyze.py - 自动分析器
"""
从 events.jsonl 分析，产出结构化报告：
  metrics / top_issues / alias_suggestions / tool_suggestions / threshold_warnings
"""

import json, time, sys, math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, count_by_type
from core.config import get_int, get_float

AIOS_ROOT = Path(__file__).resolve().parent.parent
LEARNING_DIR = AIOS_ROOT / "learning"
LEARNING_DIR.mkdir(exist_ok=True)

CORRECTION_THRESHOLD = get_int("analysis.correction_threshold", 3)
LOW_SCORE_THRESHOLD = get_float("analysis.low_score_threshold", 0.80)

# 时间衰减: W = e^(-λ * Δt), λ = ln(2)/half_life_hours
DECAY_HALF_LIFE_HOURS = 12  # 12h 半衰期
DECAY_LAMBDA = math.log(2) / (DECAY_HALF_LIFE_HOURS * 3600)


def _decay_weight(event_ts: int) -> float:
    """指数衰减权重，越近的事件权重越大"""
    dt = max(0, time.time() - event_ts)
    return math.exp(-DECAY_LAMBDA * dt)


def compute_metrics(days: int = 1) -> dict:
    events = load_events(days)

    # v0.2: 按层分类（兼容 v0.1 旧格式）
    layer_map = {
        "tool": "TOOL",
        "task": "TOOL",
        "match": "MEM",
        "correction": "MEM",
        "confirm": "MEM",
        "lesson": "MEM",
        "error": "SEC",
        "http_error": "SEC",
        "health": "KERNEL",
        "deploy": "KERNEL",
    }

    by_layer = {"KERNEL": [], "COMMS": [], "TOOL": [], "MEM": [], "SEC": []}
    for e in events:
        layer = e.get("layer")
        if not layer:
            # v0.1 兼容
            old_type = e.get("type", "")
            v1_type = (e.get("payload") or {}).get("_v1_type", "")
            layer = layer_map.get(old_type) or layer_map.get(v1_type) or "TOOL"
        if layer not in by_layer:
            layer = "TOOL"
        by_layer[layer].append(e)

    # 从各层提取指标
    tools = by_layer["TOOL"]
    mem_events = by_layer["MEM"]
    sec_events = by_layer["SEC"]

    # 匹配/纠正（MEM 层）
    matches = [e for e in mem_events if _event_name(e) in ("match", "confirm")]
    corrections = [e for e in mem_events if _event_name(e) == "correction"]
    total_match = len(matches) + len(corrections)
    correction_rate = len(corrections) / total_match if total_match > 0 else 0

    # 工具成功率
    tool_ok = [t for t in tools if _is_ok(t)]
    tool_success_rate = len(tool_ok) / len(tools) if tools else 1.0

    # HTTP 错误（SEC 层）
    http_errors = [e for e in sec_events if _event_name(e) == "http_error"]
    http_codes = Counter(_payload(e).get("status_code", "?") for e in http_errors)

    # p95 + p50 per tool
    by_tool = defaultdict(list)
    for e in tools:
        name = _tool_name(e)
        ms = _latency(e)
        if ms > 0:
            by_tool[name].append(ms)

    tool_p95 = {}
    tool_p50 = {}
    for name, times in by_tool.items():
        if len(times) >= 2:
            s = sorted(times)
            tool_p95[name] = s[math.ceil(0.95 * len(s)) - 1]
            tool_p50[name] = s[len(s) // 2]

    return {
        "counts": {
            "events": len(events),
            "matches": len(matches),
            "corrections": len(corrections),
            "tools": len(tools),
            "by_layer": {k: len(v) for k, v in by_layer.items()},
        },
        "quality": {
            "correction_rate": round(correction_rate, 4),
        },
        "reliability": {
            "tool_success_rate": round(tool_success_rate, 4),
            "http_502": http_codes.get(502, 0),
            "http_404": http_codes.get(404, 0),
        },
        "performance": {
            "tool_p95_ms": tool_p95,
            "tool_p50_ms": tool_p50,
        },
    }


# ── v0.2 辅助函数：统一从新旧 schema 提取字段 ──


def _event_name(e: dict) -> str:
    """提取事件名（兼容 v0.1 type 和 v0.2 event）"""
    name = e.get("event", "")
    if name:
        # v0.2 event 可能是 "tool_exec" 或 "correction"
        # 去掉 v0.1 兼容层加的前缀
        for prefix in ("tool_", ""):
            pass
        return name
    return (e.get("payload") or {}).get("_v1_type", e.get("type", ""))


def _is_ok(e: dict) -> bool:
    """判断事件是否成功"""
    if e.get("status") == "err":
        return False
    payload = e.get("payload", e.get("data", {}))
    return payload.get("ok", True)


def _tool_name(e: dict) -> str:
    """提取工具名"""
    payload = e.get("payload", e.get("data", {}))
    return payload.get(
        "name", payload.get("tool", e.get("source", e.get("event", "?")))
    )


def _latency(e: dict) -> int:
    """提取延迟"""
    ms = e.get("latency_ms", 0)
    if ms:
        return ms
    payload = e.get("payload", e.get("data", {}))
    return payload.get("ms", payload.get("elapsed_ms", 0))


def _payload(e: dict) -> dict:
    """提取 payload（兼容 v0.1 data 和 v0.2 payload）"""
    return e.get("payload", e.get("data", {}))


def compute_top_issues(days: int = 7) -> dict:
    events = load_events(days)
    corrections = [e for e in events if _event_name(e) == "correction"]
    errors = [
        e
        for e in events
        if e.get("status") == "err" or _event_name(e) in ("runtime_error", "http_error")
    ]
    failed_tools = [
        e
        for e in events
        if e.get("layer", e.get("type")) in ("TOOL", "tool", "task") and not _is_ok(e)
    ]

    return {
        "top_corrected_inputs": dict(
            Counter(
                _payload(e).get("query", _payload(e).get("input", "?"))
                for e in corrections
            ).most_common(10)
        ),
        "top_failed_tools": dict(
            Counter(_tool_name(e) for e in failed_tools).most_common(5)
        ),
        "top_error_types": dict(
            Counter(
                (
                    f"http_{_payload(e).get('status_code', '?')}"
                    if _event_name(e) == "http_error"
                    else _payload(e).get("error", e.get("event", "?"))[:50]
                )
                for e in errors
            ).most_common(5)
        ),
    }


def compute_alias_suggestions(days: int = 7) -> list:
    """L1: alias 建议（可自动应用）"""
    corrections = load_events(days, "correction")
    targets = defaultdict(list)
    examples = defaultdict(list)

    for c in corrections:
        data = c.get("data", {})
        inp = data.get("input", "")
        target = data.get("correct_target", "")
        matched = data.get("matched", "")
        if inp and target:
            targets[inp].append(target)
            if matched:
                ex = f"{matched}->{target}"
                if ex not in examples[inp]:
                    examples[inp].append(ex)

    suggestions = []
    for inp, tlist in targets.items():
        tc = Counter(tlist)
        top, count = tc.most_common(1)[0]
        if count >= CORRECTION_THRESHOLD:
            suggestions.append(
                {
                    "level": "L1",
                    "input": inp,
                    "suggested": top,
                    "confidence": round(count / len(tlist), 2),
                    "evidence": {
                        "corrections": count,
                        "examples": examples[inp][:3],
                    },
                    "reason": f"corrected>={count}",
                }
            )

    return suggestions


def compute_tool_suggestions(days: int = 7) -> list:
    """L2: tool 建议 — 失败驱动 + 性能驱动"""
    events = load_events(days)
    tool_events = [
        e
        for e in events
        if e.get("layer") == "TOOL" or e.get("type") in ("tool", "task")
    ]
    failed = [
        e
        for e in events
        if not _is_ok(e)
        and (
            e.get("layer") in ("TOOL", "SEC")
            or e.get("type") in ("tool", "task", "error", "http_error")
        )
    ]

    # --- Failure Learner ---
    by_tool_fail = defaultdict(list)
    for e in failed:
        tool = _tool_name(e)
        by_tool_fail[tool].append(e)

    suggestions = []
    for tool, errs in by_tool_fail.items():
        if len(errs) < 2:
            continue
        err_types = Counter()
        for e in errs:
            p = _payload(e)
            code = p.get("status_code", "")
            err = p.get("err", p.get("error", ""))
            err_types[str(code) if code else err[:50] or "unknown"] += 1
        top_err, _ = err_types.most_common(1)[0]

        suggestions.append(
            {
                "level": "L2",
                "name": tool,
                "action": "cooldown_10m" if len(errs) >= 3 else "monitor",
                "confidence": round(min(len(errs) / 5, 1.0), 2),
                "evidence": {"fails": len(errs), "top_err": top_err},
                "reason": f"repeat_fail>={len(errs)}",
            }
        )

    # --- Perf Learner ---
    by_tool_perf = defaultdict(list)
    for e in tool_events:
        tool = _tool_name(e)
        ms = _latency(e)
        if ms > 0:
            by_tool_perf[tool].append(ms)

    for tool, times in by_tool_perf.items():
        if len(times) < 3:
            continue
        times_sorted = sorted(times)
        p95_idx = math.ceil(0.95 * len(times_sorted)) - 1
        p95 = times_sorted[p95_idx]
        median = times_sorted[len(times_sorted) // 2]

        if p95 > 5000:  # p95 > 5s
            suggestions.append(
                {
                    "level": "L2",
                    "name": tool,
                    "action": "optimize_or_cache",
                    "confidence": round(min(p95 / 10000, 1.0), 2),
                    "evidence": {
                        "p95_ms": p95,
                        "median_ms": median,
                        "samples": len(times),
                    },
                    "reason": f"p95>{p95}ms",
                }
            )

    return suggestions


def compute_threshold_warnings(days: int = 7) -> list:
    """L3: 阈值警告（仅报警）"""
    events = load_events(days)
    matches = [e for e in events if e.get("type") == "match"]
    corrections = [e for e in events if e.get("type") == "correction"]
    warnings = []

    total = len(matches) + len(corrections)
    if total > 0:
        cr = len(corrections) / total
        if cr > 0.15:
            warnings.append(
                {
                    "field": "correction_rate",
                    "current": round(cr, 2),
                    "suggested": 0.10,
                    "reason": "high_correction_rate",
                }
            )

    if matches:
        low = [
            m
            for m in matches
            if (m.get("data") or {}).get("score", 1.0) < LOW_SCORE_THRESHOLD
        ]
        lsr = len(low) / len(matches)
        if lsr > 0.15:
            warnings.append(
                {
                    "field": "low_score_rate",
                    "current": round(lsr, 2),
                    "suggested": 0.10,
                    "reason": "too_many_low_score_matches",
                }
            )

    return warnings


def _get_git_commit() -> str:
    try:
        import subprocess, os

        git_exe = r"C:\Program Files\Git\cmd\git.exe"
        r = subprocess.run(
            [git_exe, "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
            cwd=os.path.join(
                os.environ.get("USERPROFILE", ""), ".openclaw", "workspace"
            ),
        )
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


AIOS_VERSION = "0.2.0"


def generate_full_report(days: int = 7) -> dict:
    """完整结构化报告"""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    window_from = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - days * 86400)
    )

    metrics = compute_metrics(days)

    report = {
        "ts": now,
        "window": {"from": window_from, "to": now},
        **metrics,
        "model": {"default": "claude-sonnet-4-6", "fallback": "claude-opus-4-6"},
        "version": {"aios": AIOS_VERSION, "commit": _get_git_commit()},
        "top_issues": compute_top_issues(days),
        "alias_suggestions": compute_alias_suggestions(days),
        "tool_suggestions": compute_tool_suggestions(days),
        "threshold_warnings": compute_threshold_warnings(days),
    }

    # 写 suggestions.json
    sug = {
        "generated_at": now,
        "alias_suggestions": [
            {
                "input": s["input"],
                "suggested": s["suggested"],
                "reason": s["reason"],
                "confidence": s["confidence"],
            }
            for s in report["alias_suggestions"]
        ],
        "threshold_warnings": report["threshold_warnings"],
        "route_suggestions": [],
    }
    (LEARNING_DIR / "suggestions.json").write_text(
        json.dumps(sug, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return report


def generate_daily_report(days: int = 1) -> str:
    r = generate_full_report(days)

    # 基线固化
    try:
        from learning.baseline import snapshot

        snapshot(days)
    except Exception:
        pass

    # 门禁检测
    gate_result = None
    try:
        from learning.guardrail import guardrail_from_history
        from learning.baseline import load_history
        from learning.tickets import ingest

        history = load_history(30)
        gate_tickets = guardrail_from_history(history)
        if gate_tickets:
            ingest(
                [
                    {
                        "level": t.level,
                        "name": t.title,
                        "action": "investigate",
                        "reason": t.evidence.get("rule", ""),
                        "confidence": 0.8,
                        "evidence": t.evidence,
                    }
                    for t in gate_tickets
                ]
            )
        gate_result = {
            "alerts": [
                {"title": t.title, "evidence": t.evidence} for t in gate_tickets
            ],
            "status": "regression_detected" if gate_tickets else "gate_passed",
        }
    except Exception:
        pass

    # L2 → 工单
    try:
        from learning.tickets import ingest

        ingest(r.get("tool_suggestions", []))
    except Exception:
        pass

    m = r
    q = m.get("quality", {})
    rel = m.get("reliability", {})
    perf = m.get("performance", {})
    counts = m.get("counts", {})
    lines = [
        f"# AIOS Daily Report",
        f"Generated: {r['ts']}",
        f"Window: {r['window']['from']} → {r['window']['to']}\n",
        "## A. Metrics",
        f"- events: {counts.get('events', 0)}  matches: {counts.get('matches', 0)}  corrections: {counts.get('corrections', 0)}  tools: {counts.get('tools', 0)}",
        f"- correction_rate: {q.get('correction_rate', 0):.2%}",
        f"- tool_success_rate: {rel.get('tool_success_rate', 0):.2%}",
        f"- http_502: {rel.get('http_502', 0)}  http_404: {rel.get('http_404', 0)}",
    ]
    if perf.get("tool_p95_ms"):
        lines.append("- p95/p50:")
        for t in perf["tool_p95_ms"]:
            p95 = perf["tool_p95_ms"].get(t, "?")
            p50 = perf.get("tool_p50_ms", {}).get(t, "?")
            lines.append(f"  - {t}: p95={p95}ms p50={p50}ms")

    lines.append("\n## B. Top Issues")
    for inp, cnt in r["top_issues"].get("top_corrected_inputs", {}).items():
        lines.append(f'- corrected: "{inp}" x{cnt}')
    for t, cnt in r["top_issues"].get("top_failed_tools", {}).items():
        lines.append(f"- failed: {t} x{cnt}")

    lines.append("\n## C. Alias Suggestions (L1)")
    for s in r["alias_suggestions"]:
        lines.append(
            f"- \"{s['input']}\" → \"{s['suggested']}\" conf={s['confidence']} ({s['reason']})"
        )

    lines.append("\n## D. Tool Suggestions (L2)")
    for s in r["tool_suggestions"]:
        lines.append(
            f"- {s['name']}: {s['action']} conf={s['confidence']} ({s['reason']})"
        )

    if r["threshold_warnings"]:
        lines.append("\n## E. Threshold Warnings")
        for w in r["threshold_warnings"]:
            lines.append(f"- {w['field']}: {w['current']} → {w['suggested']}")

    if not any(
        [r["alias_suggestions"], r["tool_suggestions"], r["threshold_warnings"]]
    ):
        lines.append("\n- No suggestions")

    # evolution score
    try:
        from learning.baseline import evolution_score

        evo = evolution_score()
        lines.append(f"\n## F. Evolution Score")
        lines.append(f"- score: {evo['score']}  grade: {evo['grade']}")
        bd = evo.get("breakdown", {})
        for k, v in bd.items():
            lines.append(f"  - {k}: {v['value']} (w={v['weight']})")
    except Exception:
        pass

    # regression gate
    if gate_result and gate_result.get("alerts"):
        lines.append(f"\n## G. Regression Gate ⚠")
        for a in gate_result["alerts"]:
            lines.append(f"- {a['title']}: {a['evidence'].get('rule', '')}")
    elif gate_result:
        lines.append(f"\n## G. Regression Gate ✓")
        lines.append(f"- {gate_result['status']}")

    report_text = "\n".join(lines)
    (LEARNING_DIR / "daily_report.md").write_text(report_text, encoding="utf-8")
    return report_text


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "report"
    if action == "json":
        print(json.dumps(generate_full_report(), ensure_ascii=False, indent=2))
    elif action == "suggestions":
        r = generate_full_report()
        sug = {
            k: r[k]
            for k in ("alias_suggestions", "tool_suggestions", "threshold_warnings")
        }
        sug["generated_at"] = r["generated_at"]
        print(json.dumps(sug, ensure_ascii=False, indent=2))
    elif action == "report":
        print(generate_daily_report())
    else:
        print("Usage: analyze.py [json|suggestions|report]")
