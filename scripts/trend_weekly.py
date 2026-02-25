#!/usr/bin/env python3
"""
AIOS 周趋势分析 v1.0
逐日指标快照 + 错误收敛/发散分析 + 方向箭头

用法:
  python -m aios.scripts.trend_weekly                    # 过去7天周报
  python -m aios.scripts.trend_weekly --days 14          # 自定义天数
  python -m aios.scripts.trend_weekly --format telegram  # 精简版
  python -m aios.scripts.trend_weekly --save             # 保存到 reports/
"""

import json, math, sys, time, argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.engine import load_events, VALID_LAYERS
from core.config import get_path

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


# ── 工具函数 ──


def _day_key(epoch: float) -> str:
    return time.strftime("%m-%d", time.localtime(epoch))


def _day_full(epoch: float) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(epoch))


def _payload(e: dict) -> dict:
    return e.get("payload", e.get("data", {}))


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
        "health": "KERNEL",
        "deploy": "KERNEL",
    }
    return mapping.get(t, "TOOL")


def _is_ok(e: dict) -> bool:
    if e.get("status") == "err":
        return False
    return _payload(e).get("ok", True)


def _event_name(e: dict) -> str:
    return e.get("event", _payload(e).get("_v1_type", e.get("type", "?")))


def _latency(e: dict) -> int:
    ms = e.get("latency_ms", 0)
    if ms:
        return ms
    p = _payload(e)
    return p.get("ms", p.get("elapsed_ms", p.get("duration_ms", 0)))


def _p95(values: list) -> int:
    if not values:
        return 0
    s = sorted(values)
    return s[math.ceil(0.95 * len(s)) - 1] if len(s) >= 2 else s[0]


def _trend_arrow(values: list) -> str:
    """根据序列趋势返回方向箭头"""
    if len(values) < 2:
        return "→"
    first_half = sum(values[: len(values) // 2]) / max(len(values) // 2, 1)
    second_half = sum(values[len(values) // 2 :]) / max(
        len(values) - len(values) // 2, 1
    )
    if first_half == 0:
        return "→" if second_half == 0 else "↑"
    pct = (second_half - first_half) / first_half * 100
    if pct > 15:
        return "↑"
    elif pct < -15:
        return "↓"
    return "→"


def _sparkline(values: list) -> str:
    """简易 sparkline（用 Unicode block 字符）"""
    if not values:
        return ""
    blocks = " ▁▂▃▄▅▆▇█"
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    return "".join(blocks[min(int((v - mn) / rng * 8), 8)] for v in values)


# ── 核心分析 ──


def compute_daily_metrics(events: list, days: int) -> list:
    """按天分桶，计算每天的指标"""
    now = time.time()
    buckets = defaultdict(list)
    for e in events:
        epoch = e.get("epoch", 0)
        if epoch <= 0:
            continue
        buckets[_day_full(epoch)].append(e)

    # 生成连续日期序列
    result = []
    for i in range(days - 1, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_events = buckets.get(day, [])
        total = len(day_events)

        # TSR
        tools = [e for e in day_events if _layer(e) == "TOOL"]
        tool_ok = sum(1 for t in tools if _is_ok(t))
        tsr = tool_ok / len(tools) * 100 if tools else 100.0

        # 层分布
        layer_counts = Counter(_layer(e) for e in day_events)

        # 延迟
        latencies = [_latency(e) for e in day_events if _latency(e) > 0]
        avg_lat = round(sum(latencies) / len(latencies)) if latencies else 0
        p95_lat = _p95(latencies)

        # 错误事件
        errors = [e for e in day_events if not _is_ok(e)]
        error_types = Counter(_event_name(e) for e in errors)

        # MEM 盲区
        mem_events = [e for e in day_events if _layer(e) == "MEM"]
        misses = sum(1 for e in mem_events if "miss" in _event_name(e))

        result.append(
            {
                "date": day,
                "date_short": day[5:],  # MM-DD
                "total": total,
                "tsr": round(tsr, 1),
                "layer_counts": dict(layer_counts),
                "avg_latency": avg_lat,
                "p95_latency": p95_lat,
                "errors": dict(error_types),
                "error_count": len(errors),
                "mem_misses": misses,
            }
        )

    return result


def analyze_error_convergence(daily: list) -> list:
    """分析错误类型的收敛/发散趋势"""
    # 收集所有出现过的错误类型
    all_error_types = set()
    for d in daily:
        all_error_types.update(d["errors"].keys())

    results = []
    for err_type in sorted(all_error_types):
        counts = [d["errors"].get(err_type, 0) for d in daily]
        total = sum(counts)
        trend = _trend_arrow(counts)

        # 判断状态
        if total == 0:
            status = "已消除"
        elif trend == "↓":
            status = "收敛中"
        elif trend == "↑":
            status = "发散中"
        else:
            status = "稳定"

        results.append(
            {
                "type": err_type,
                "total": total,
                "trend": trend,
                "status": status,
                "daily": counts,
                "spark": _sparkline(counts),
            }
        )

    # 按严重程度排序：发散 > 稳定 > 收敛 > 已消除
    priority = {"发散中": 0, "稳定": 1, "收敛中": 2, "已消除": 3}
    results.sort(key=lambda x: (priority.get(x["status"], 9), -x["total"]))
    return results


def generate_weekly_report(days: int = 7, compact: bool = False) -> str:
    events = load_events(days)
    daily = compute_daily_metrics(events, days)
    error_conv = analyze_error_convergence(daily)

    now = time.strftime("%Y-%m-%d %H:%M")
    total_events = sum(d["total"] for d in daily)

    # 趋势数据
    tsr_values = [d["tsr"] for d in daily if d["total"] > 0]
    vol_values = [d["total"] for d in daily]
    lat_values = [d["avg_latency"] for d in daily if d["avg_latency"] > 0]
    miss_values = [d["mem_misses"] for d in daily]

    tsr_trend = _trend_arrow(tsr_values)
    vol_trend = _trend_arrow(vol_values)
    lat_trend = _trend_arrow(lat_values)
    miss_trend = _trend_arrow(miss_values)

    avg_tsr = round(sum(tsr_values) / len(tsr_values), 1) if tsr_values else 100.0
    avg_vol = round(sum(vol_values) / len(vol_values), 1)

    if compact:
        # Telegram 精简版
        lines = [
            f"📊 AIOS 周趋势 | {now}",
            f"窗口: {days}天 | 总事件: {total_events}",
            "",
            f"TSR: {avg_tsr}% {tsr_trend} {_sparkline(tsr_values)}",
            f"事件量: 日均{avg_vol:.0f} {vol_trend} {_sparkline(vol_values)}",
        ]
        if lat_values:
            avg_lat = round(sum(lat_values) / len(lat_values))
            lines.append(f"延迟: 均{avg_lat}ms {lat_trend}")
        lines.append(f"记忆盲区: {sum(miss_values)}次 {miss_trend}")

        # 错误收敛
        diverging = [e for e in error_conv if e["status"] == "发散中"]
        converging = [e for e in error_conv if e["status"] == "收敛中"]
        if diverging:
            lines.append("")
            lines.append("⚠️ 发散中的错误:")
            for e in diverging[:5]:
                lines.append(
                    f"  {e['trend']} {e['type']} ({e['total']}次) {e['spark']}"
                )
        if converging:
            lines.append("")
            lines.append("✅ 收敛中的错误:")
            for e in converging[:5]:
                lines.append(
                    f"  {e['trend']} {e['type']} ({e['total']}次) {e['spark']}"
                )

        if not error_conv:
            lines.append("\n✅ 无错误事件")

        return "\n".join(lines)

    # 完整 Markdown 版
    lines = [
        f"# 📊 AIOS 周趋势报告",
        f"生成时间: {now} | 窗口: {days}天 | 总事件: {total_events}",
        "",
        "## 1. 关键指标趋势",
        "",
        f"| 指标 | 均值 | 趋势 | 火花图 |",
        f"| :--- | ---: | :---: | :--- |",
        f"| TSR | {avg_tsr}% | {tsr_trend} | {_sparkline(tsr_values)} |",
        f"| 日事件量 | {avg_vol:.0f} | {vol_trend} | {_sparkline(vol_values)} |",
    ]
    if lat_values:
        avg_lat = round(sum(lat_values) / len(lat_values))
        lines.append(
            f"| 平均延迟 | {avg_lat}ms | {lat_trend} | {_sparkline(lat_values)} |"
        )
    lines.append(
        f"| 记忆盲区 | {sum(miss_values)}次 | {miss_trend} | {_sparkline(miss_values)} |"
    )

    # 逐日明细
    lines.extend(
        [
            "",
            "## 2. 逐日明细",
            "",
            "| 日期 | 事件 | TSR | 错误 | 盲区 | 延迟(avg) |",
            "| :--- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for d in daily:
        lines.append(
            f"| {d['date_short']} | {d['total']} | {d['tsr']}% | "
            f"{d['error_count']} | {d['mem_misses']} | {d['avg_latency']}ms |"
        )

    # 错误收敛分析
    lines.extend(
        [
            "",
            "## 3. 错误收敛分析",
            "",
        ]
    )
    if error_conv:
        lines.append("| 错误类型 | 总次数 | 趋势 | 状态 | 分布 |")
        lines.append("| :--- | ---: | :---: | :--- | :--- |")
        for e in error_conv:
            lines.append(
                f"| {e['type']} | {e['total']} | {e['trend']} | {e['status']} | {e['spark']} |"
            )
    else:
        lines.append("✅ 过去 {days} 天无错误事件")

    # 层分布趋势
    lines.extend(
        [
            "",
            "## 4. 层分布趋势",
            "",
        ]
    )
    for layer_name in ["KERNEL", "COMMS", "TOOL", "MEM", "SEC"]:
        vals = [d["layer_counts"].get(layer_name, 0) for d in daily]
        lines.append(
            f"- {layer_name}: {_sparkline(vals)} {_trend_arrow(vals)} (总{sum(vals)})"
        )

    lines.extend(
        [
            "",
            "---",
            f"*Generated by AIOS Trend Weekly v1.0 | {now}*",
        ]
    )

    return "\n".join(lines)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="AIOS 周趋势分析")
    p.add_argument("--days", type=int, default=7, help="分析窗口（天）")
    p.add_argument("--format", choices=["markdown", "telegram"], default="markdown")
    p.add_argument("--save", action="store_true", help="保存到 reports/")
    args = p.parse_args()

    report = generate_weekly_report(args.days, compact=(args.format == "telegram"))
    print(report)

    if args.save:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out = REPORTS_DIR / f"trend_weekly_{ts}.md"
        out.write_text(report, encoding="utf-8")
        print(f"\n💾 已保存: {out}")


if __name__ == "__main__":
    main()
