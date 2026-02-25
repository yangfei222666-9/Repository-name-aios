# aios/scripts/reflect.py - 晨间反思：从简报数据自动生成每日策略
"""
读取 insight 简报数据，用规则引擎（非 LLM）提取可执行策略。
不依赖外部 API，纯本地运行。

用法：
  python -m aios.scripts.reflect              # 基于今日 insight 数据
  python -m aios.scripts.reflect --days 1      # 指定窗口
"""

import json, sys, time, math
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, emit, LAYER_KERNEL, LAYER_MEM, VALID_LAYERS
from core.config import get_path

LEARNING_DIR = Path(__file__).resolve().parent.parent / "learning"
STRATEGIES_FILE = LEARNING_DIR / "strategies.jsonl"


def _p95(values: list) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[math.ceil(0.95 * len(s)) - 1] if len(s) >= 2 else s[0]


def _payload(e: dict) -> dict:
    return e.get("payload", e.get("data", {}))


def _latency(e: dict) -> int:
    ms = e.get("latency_ms", 0)
    if ms:
        return ms
    p = _payload(e)
    return p.get("ms", p.get("elapsed_ms", 0))


def _is_ok(e: dict) -> bool:
    if e.get("status") == "err":
        return False
    return _payload(e).get("ok", True)


def _layer(e: dict) -> str:
    l = e.get("layer", "")
    if l in VALID_LAYERS:
        return l
    t = e.get("type", "")
    mapping = {
        "tool": "TOOL",
        "task": "TOOL",
        "match": "MEM",
        "correction": "MEM",
        "error": "SEC",
        "http_error": "SEC",
    }
    return mapping.get(t, "TOOL")


def analyze_and_reflect(days: int = 1) -> list:
    """分析事件数据，返回策略列表"""
    events = load_events(days)
    if not events:
        return []

    strategies = []

    # ── 按层分类 ──
    by_layer = defaultdict(list)
    for e in events:
        by_layer[_layer(e)].append(e)

    tools = by_layer["TOOL"]
    sec = by_layer["SEC"]
    mem = by_layer["MEM"]

    # ══════════════════════════════════════════════
    #  规则 1: TSR 低于 90% → 找出失败最多的工具
    # ══════════════════════════════════════════════
    if tools:
        tool_ok = sum(1 for t in tools if _is_ok(t))
        tsr = tool_ok / len(tools) * 100

        if tsr < 90:
            # 找失败最多的工具
            fail_counts = defaultdict(int)
            for t in tools:
                if not _is_ok(t):
                    p = _payload(t)
                    name = p.get("name", t.get("event", "?"))
                    fail_counts[name] += 1

            if fail_counts:
                worst = max(fail_counts, key=fail_counts.get)
                strategies.append(
                    {
                        "topic": "daily_strategy",
                        "rule": "low_tsr",
                        "priority": "high",
                        "content": f"TSR={tsr:.1f}%，{worst} 失败 {fail_counts[worst]} 次。"
                        f"今天使用 {worst} 前先检查参数有效性，失败时立即换备选方案。",
                        "evidence": {
                            "tsr": round(tsr, 1),
                            "worst_tool": worst,
                            "fail_count": fail_counts[worst],
                        },
                    }
                )

    # ══════════════════════════════════════════════
    #  规则 2: 某工具 p95 > 5s → 建议优化或缓存
    # ══════════════════════════════════════════════
    by_tool_latency = defaultdict(list)
    for e in tools:
        p = _payload(e)
        name = p.get("name", e.get("event", "?"))
        ms = _latency(e)
        if ms > 0:
            by_tool_latency[name].append(ms)

    for name, times in by_tool_latency.items():
        p95 = _p95(times)
        if p95 > 5000:
            strategies.append(
                {
                    "topic": "daily_strategy",
                    "rule": "slow_tool",
                    "priority": "medium",
                    "content": f"{name} p95={p95}ms 过慢。"
                    f"今天尽量减少 {name} 调用，优先用本地数据/缓存替代。",
                    "evidence": {
                        "tool": name,
                        "p95_ms": p95,
                        "calls": len(times),
                        "median_ms": sorted(times)[len(times) // 2],
                    },
                }
            )

    # ══════════════════════════════════════════════
    #  规则 3: SEC 层有致命事件 → 今天优先修复
    # ══════════════════════════════════════════════
    critical_events = [
        e
        for e in sec
        if e.get("event", "") in ("system_crash", "circuit_breaker_tripped")
    ]
    if critical_events:
        strategies.append(
            {
                "topic": "daily_strategy",
                "rule": "critical_sec",
                "priority": "critical",
                "content": f"昨天有 {len(critical_events)} 个致命安全事件。"
                f"今天第一优先级：排查并修复这些崩溃，其他任务延后。",
                "evidence": {
                    "critical_count": len(critical_events),
                    "events": [e.get("event") for e in critical_events[:3]],
                },
            }
        )

    # ══════════════════════════════════════════════
    #  规则 4: MEM miss 率高 → 知识盲区需要补充
    # ══════════════════════════════════════════════
    mem_reads = [
        e
        for e in mem
        if any(
            k in (e.get("event", "")) for k in ("recall", "match", "confirm", "miss")
        )
    ]
    mem_misses = [e for e in mem if "miss" in (e.get("event", ""))]
    if mem_reads and len(mem_misses) / len(mem_reads) > 0.3:
        strategies.append(
            {
                "topic": "daily_strategy",
                "rule": "high_miss_rate",
                "priority": "medium",
                "content": f"记忆未命中率 {len(mem_misses)}/{len(mem_reads)} = "
                f"{len(mem_misses)/len(mem_reads):.0%}。"
                f"今天遇到新知识时主动写入 lessons，补充知识盲区。",
                "evidence": {
                    "miss_count": len(mem_misses),
                    "read_count": len(mem_reads),
                },
            }
        )

    # ══════════════════════════════════════════════
    #  规则 5: 纠正率高 → 需要更谨慎
    # ══════════════════════════════════════════════
    corrections = [e for e in mem if "correction" in (e.get("event", ""))]
    matches = [
        e for e in mem if any(k in (e.get("event", "")) for k in ("match", "confirm"))
    ]
    total_match = len(matches) + len(corrections)
    if total_match > 0:
        cr = len(corrections) / total_match
        if cr > 0.15:
            strategies.append(
                {
                    "topic": "daily_strategy",
                    "rule": "high_correction_rate",
                    "priority": "high",
                    "content": f"纠正率 {cr:.0%} 偏高。"
                    f"今天回答前多检查一遍，不确定的事情先查证再说。",
                    "evidence": {
                        "correction_rate": round(cr, 2),
                        "corrections": len(corrections),
                        "total": total_match,
                    },
                }
            )

    # ══════════════════════════════════════════════
    #  规则 6: 一切正常 → 鼓励
    # ══════════════════════════════════════════════
    if not strategies:
        strategies.append(
            {
                "topic": "daily_strategy",
                "rule": "all_clear",
                "priority": "low",
                "content": "昨天表现良好，各项指标正常。保持节奏，继续进化。",
                "evidence": {},
            }
        )

    return strategies


def save_strategies(strategies: list):
    """追加策略到 strategies.jsonl"""
    STRATEGIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    date = time.strftime("%Y-%m-%d")
    for s in strategies:
        record = {
            "ts": ts,
            "date": date,
            **s,
        }
        with STRATEGIES_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 记录反思事件到 events.jsonl
    emit(
        LAYER_KERNEL,
        "reflection_complete",
        "ok",
        payload={
            "strategy_count": len(strategies),
            "priorities": [s["priority"] for s in strategies],
        },
    )


def load_today_strategies() -> list:
    """加载今天的策略（供 Agent 启动时注入）"""
    if not STRATEGIES_FILE.exists():
        return []
    today = time.strftime("%Y-%m-%d")
    strategies = []
    for line in STRATEGIES_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            s = json.loads(line)
            if s.get("date") == today and s.get("topic") == "daily_strategy":
                strategies.append(s)
        except Exception:
            continue
    return strategies


def format_strategies_for_prompt(strategies: list) -> str:
    """格式化策略为可注入 System Prompt 的文本"""
    if not strategies:
        return ""
    lines = ["[今日特别指令 (由昨天的数据自动生成)]"]
    for s in strategies:
        icon = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "✅"}.get(
            s["priority"], "📋"
        )
        lines.append(f"{icon} [{s['rule']}] {s['content']}")
    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    import argparse

    p = argparse.ArgumentParser(description="AIOS 晨间反思")
    p.add_argument("--days", type=int, default=1, help="分析窗口（天）")
    p.add_argument("--inject", action="store_true", help="只输出今日策略（供注入）")
    args = p.parse_args()

    if args.inject:
        strategies = load_today_strategies()
        if strategies:
            print(format_strategies_for_prompt(strategies))
        else:
            print("今天暂无策略。")
        return

    print("🧠 正在进行晨间反思...")
    strategies = analyze_and_reflect(args.days)
    save_strategies(strategies)

    print(f"\n📋 生成 {len(strategies)} 条策略：")
    for s in strategies:
        icon = {"critical": "🚨", "high": "⚠️", "medium": "📋", "low": "✅"}.get(
            s["priority"], "📋"
        )
        print(f"  {icon} [{s['rule']}] {s['content']}")

    print(f"\n已写入: {STRATEGIES_FILE}")


if __name__ == "__main__":
    main()
