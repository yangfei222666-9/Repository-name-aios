# aios/scripts/insight.py - 穷人版 ClickHouse：每日健康简报
"""
读取 events.jsonl，生成 Markdown 简报。
不依赖 Pandas，不依赖外部服务，纯 Python 原生。

用法：
  python -m aios.scripts.insight          # 过去 24h
  python -m aios.scripts.insight --days 7 # 过去 7 天
  python -m aios.scripts.insight --out telegram  # 输出到 telegram（精简版）
"""

import json, math, sys, time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, count_by_layer, VALID_LAYERS
from core.config import get_path

LEARNING_DIR = Path(__file__).resolve().parent.parent / "learning"


def _p95(values: list) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[math.ceil(0.95 * len(s)) - 1] if len(s) >= 2 else s[0]


def _p50(values: list) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[len(s) // 2]


def _event_name(e: dict) -> str:
    return e.get("event", (e.get("payload") or {}).get("_v1_type", e.get("type", "?")))


def _payload(e: dict) -> dict:
    return e.get("payload", e.get("data", {}))


def _latency(e: dict) -> int:
    ms = e.get("latency_ms", 0)
    if ms:
        return ms
    p = _payload(e)
    return p.get("ms", p.get("elapsed_ms", p.get("duration_ms", 0)))


def _is_ok(e: dict) -> bool:
    if e.get("status") == "err":
        return False
    return _payload(e).get("ok", True)


def _layer(e: dict) -> str:
    l = e.get("layer", "")
    if l in VALID_LAYERS:
        return l
    # v0.1 兼容
    t = e.get("type", "")
    mapping = {
        "tool": "TOOL",
        "task": "TOOL",
        "match": "MEM",
        "correction": "MEM",
        "error": "SEC",
        "http_error": "SEC",
        "health": "KERNEL",
        "deploy": "KERNEL",
    }
    return mapping.get(t, "TOOL")


def generate_insight(days: int = 1, compact: bool = False) -> str:
    events = load_events(days)
    if not events:
        return "过去 {}h 无事件数据。".format(days * 24)

    now = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    total = len(events)

    # ── 1. 按层分类 ──
    by_layer = defaultdict(list)
    for e in events:
        by_layer[_layer(e)].append(e)

    # ── 2. KERNEL 分析：心跳 ──
    kernel = by_layer["KERNEL"]
    loops = [e for e in kernel if "loop" in _event_name(e)]
    token_events = [e for e in kernel if "token" in _event_name(e)]
    total_input_tokens = sum(_payload(e).get("input_tokens", 0) for e in token_events)
    total_output_tokens = sum(_payload(e).get("output_tokens", 0) for e in token_events)
    prune_events = [e for e in kernel if "prune" in _event_name(e)]

    # ── 3. TOOL 分析：手脚效率 ──
    tools = by_layer["TOOL"]
    tool_ok = sum(1 for t in tools if _is_ok(t))
    tool_err = len(tools) - tool_ok
    tsr = tool_ok / len(tools) * 100 if tools else 100

    by_tool_name = defaultdict(list)
    for e in tools:
        p = _payload(e)
        name = p.get("name", _event_name(e))
        ms = _latency(e)
        if ms > 0:
            by_tool_name[name].append(ms)

    tool_stats = []
    for name, times in sorted(by_tool_name.items(), key=lambda x: -_p95(x[1])):
        tool_stats.append(
            {
                "name": name,
                "calls": len(times),
                "p50": _p50(times),
                "p95": _p95(times),
                "avg": round(sum(times) / len(times)),
            }
        )

    all_latencies = [ms for times in by_tool_name.values() for ms in times]
    global_p95 = _p95(all_latencies)
    global_avg = round(sum(all_latencies) / len(all_latencies)) if all_latencies else 0

    # ── 4. SEC 分析：免疫反应 ──
    sec = by_layer["SEC"]
    sec_by_event = Counter(_event_name(e) for e in sec)
    critical = [
        e for e in sec if _event_name(e) in ("system_crash", "circuit_breaker_tripped")
    ]

    # 区分测试事件：payload 里有 sig="sig_abc" 或 test=True 的视为测试
    test_critical = [
        e
        for e in critical
        if _payload(e).get("sig") == "sig_abc" or _payload(e).get("test")
    ]
    real_critical = [e for e in critical if e not in test_critical]

    # ── 5. MEM 分析：记忆深度 ──
    mem = by_layer["MEM"]
    mem_reads = [
        e
        for e in mem
        if any(
            k in _event_name(e) for k in ("recall", "match", "confirm", "load", "miss")
        )
    ]
    mem_writes = [
        e
        for e in mem
        if any(k in _event_name(e) for k in ("store", "correction", "lesson"))
    ]
    mem_misses = [e for e in mem if "miss" in _event_name(e)]

    # ── 6. COMMS 分析：对话 ──
    comms = by_layer["COMMS"]
    user_inputs = [e for e in comms if "user_input" in _event_name(e)]
    agent_responses = [e for e in comms if "agent_response" in _event_name(e)]
    response_latencies = [_latency(e) for e in agent_responses if _latency(e) > 0]
    avg_response_ms = (
        round(sum(response_latencies) / len(response_latencies))
        if response_latencies
        else 0
    )

    # ── 7. 认知死循环检测（优化：排除部署窗口）──
    # 连续 5+ 个 KERNEL 事件没有 TOOL 产出 = 可能卡住了
    # 但排除 deploy/restart/rollout 等正常批量事件
    deadlock_warnings = 0
    excluded_deploy_restart = 0
    consecutive_kernel = 0
    consecutive_kernel_events = []

    for e in events:
        layer = _layer(e)
        event_name = _event_name(e)

        if layer == "KERNEL":
            consecutive_kernel += 1
            consecutive_kernel_events.append(e)
        elif layer == "TOOL":
            consecutive_kernel = 0
            consecutive_kernel_events = []

        if consecutive_kernel >= 5:
            # 检查是否是正常窗口：
            # 1. 部署/重启/发布
            # 2. 资源快照/反思
            # 3. Scheduler 决策
            # 4. 任务创建
            # 5. 测试事件（noop/sleep/fail）
            is_normal_window = all(
                any(
                    k in _event_name(ev).lower()
                    for k in (
                        "deploy", "restart", "rollout",
                        "resource_snapshot", "reflection",
                        "scheduler.decision", "task.", "noop", "sleep", "fail"
                    )
                )
                for ev in consecutive_kernel_events
            )

            if is_normal_window:
                excluded_deploy_restart += 1
            else:
                deadlock_warnings += 1

            consecutive_kernel = 0
            consecutive_kernel_events = []

    # ══════════════════════════════════════════════
    #  生成报告
    # ══════════════════════════════════════════════

    if compact:
        # Telegram 精简版
        lines = [
            f"📊 AIOS 简报 | {now}",
            f"事件: {total} | TSR: {tsr:.1f}%",
            f"层分布: K{len(kernel)} C{len(comms)} T{len(tools)} M{len(mem)} S{len(sec)}",
        ]
        if tool_stats:
            slowest = tool_stats[0]
            lines.append(f"最慢: {slowest['name']} p95={slowest['p95']}ms")
        if real_critical:
            lines.append(f"⚠️ 致命事件: {len(real_critical)}")
        if test_critical:
            lines.append(
                f"⚠️ 致命事件(含测试): {len(critical)} (测试{len(test_critical)})"
            )
        if deadlock_warnings:
            lines.append(f"⚠️ 疑似死循环: {deadlock_warnings}")
        if excluded_deploy_restart:
            lines.append(f"ℹ️ 已排除部署窗口: {excluded_deploy_restart}")
        lines.append(
            f"记忆: 读{len(mem_reads)} 写{len(mem_writes)} 盲区{len(mem_misses)}"
        )
        if total_input_tokens + total_output_tokens > 0:
            lines.append(f"Token: 入{total_input_tokens} 出{total_output_tokens}")
        return "\n".join(lines)

    # 完整 Markdown 版
    lines = [
        f"# 🤖 AIOS 每日健康简报",
        f"日期: {now} | 窗口: {days * 24}h | 总事件: {total}",
        "",
        "## 1. 神经系统分布",
        "",
        "| 层级 | 事件数 | 占比 |",
        "| :--- | ---: | ---: |",
    ]
    for layer_name in ["KERNEL", "COMMS", "TOOL", "MEM", "SEC"]:
        count = len(by_layer[layer_name])
        pct = count / total * 100 if total else 0
        lines.append(f"| {layer_name} | {count} | {pct:.1f}% |")

    lines.extend(
        [
            "",
            "## 2. 生命体征 (KERNEL)",
            f"- 循环次数: {len(loops)}",
            f"- Token 消耗: 输入 {total_input_tokens:,} + 输出 {total_output_tokens:,} = {total_input_tokens + total_output_tokens:,}",
            f"- 上下文裁剪: {len(prune_events)} 次",
        ]
    )
    if deadlock_warnings:
        lines.append(f"- ⚠️ 疑似认知死循环: {deadlock_warnings} 次")

    lines.extend(
        [
            "",
            "## 3. 肢体效能 (TOOL)",
            f"- 任务成功率 (TSR): {tsr:.1f}% ({tool_ok}✓ / {tool_err}✗)",
            f"- 全局延迟: avg={global_avg}ms p95={global_p95}ms",
            "",
        ]
    )
    if tool_stats:
        lines.append("| 工具 | 调用 | p50 | p95 | avg |")
        lines.append("| :--- | ---: | ---: | ---: | ---: |")
        for ts in tool_stats[:10]:
            flag = " 🐌" if ts["p95"] > 5000 else ""
            lines.append(
                f"| {ts['name']}{flag} | {ts['calls']} | {ts['p50']}ms | {ts['p95']}ms | {ts['avg']}ms |"
            )

    lines.extend(
        [
            "",
            "## 4. 免疫反应 (SEC)",
            f"- 安全事件: {len(sec)} 条",
        ]
    )
    if sec_by_event:
        for evt, cnt in sec_by_event.most_common(5):
            lines.append(f"  - {evt}: {cnt}")
    if critical:
        lines.append(f"- 🚨 致命事件: {len(critical)} 条")
    if not sec:
        lines.append("- ✅ 系统平稳，无异常")

    lines.extend(
        [
            "",
            "## 5. 认知记忆 (MEM)",
            f"- 知识提取 (Read): {len(mem_reads)} 次",
            f"- 知识固化 (Write): {len(mem_writes)} 次",
            f"- 知识盲区 (Miss): {len(mem_misses)} 次",
        ]
    )
    if mem_reads or mem_writes:
        ratio = len(mem_reads) / max(len(mem_writes), 1)
        if ratio > 5:
            lines.append("- 📖 模式: 以检索为主（经验丰富，查阅多于学习）")
        elif ratio > 1:
            lines.append("- ⚖️ 模式: 读写均衡（边学边用）")
        else:
            lines.append("- ✏️ 模式: 以学习为主（新知识密集期）")

    lines.extend(
        [
            "",
            "## 6. 对话质量 (COMMS)",
            f"- 用户输入: {len(user_inputs)} 条",
            f"- Agent 回复: {len(agent_responses)} 条",
            f"- 平均响应延迟: {avg_response_ms}ms",
        ]
    )

    lines.extend(
        [
            "",
            "---",
            "*Generated by AIOS Insight v0.2*",
        ]
    )

    return "\n".join(lines)


def main():
    import argparse

    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="AIOS 每日健康简报")
    p.add_argument("--days", type=int, default=1, help="分析窗口（天）")
    p.add_argument(
        "--out", choices=["markdown", "telegram"], default="markdown", help="输出格式"
    )
    p.add_argument("--save", action="store_true", help="保存到文件")
    args = p.parse_args()

    compact = args.out == "telegram"
    report = generate_insight(args.days, compact)
    print(report)

    if args.save and not compact:
        date_str = time.strftime("%Y-%m-%d")
        out_path = LEARNING_DIR / f"insight_{date_str}.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"\n已保存到: {out_path}")


if __name__ == "__main__":
    main()
