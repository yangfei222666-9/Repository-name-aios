#!/usr/bin/env python3
"""
AIOS 趋势对比 v1.0
三维度对比：事件量 / 结构占比 / 成功质量
阈值判定 + 超限推送

用法:
  python trend.py                  # 对比 24h vs 7d 日均
  python trend.py --save           # 保存报告到 reports/
  python trend.py --format telegram  # Telegram 格式
"""

import json, time, sys, argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.config import get_path

# ── 阈值配置 ──
THRESHOLDS = {
    "event_volume_pct": 30,  # 事件量偏差 > ±30%
    "tool_ratio_spike_pct": 20,  # TOOL 占比突增 > 20%
    "tsr_min": 0.98,  # TSR < 98%
    "latency_spike_pct": 50,  # 时延上升 > 50%
}

LAYERS = ["KERNEL", "COMMS", "TOOL", "MEM", "SEC"]


def load_events(since_hours=None):
    """加载事件，可选时间过滤"""
    p = get_path("paths.events")
    if not p or not p.exists():
        return []
    events = []
    cutoff = time.time() - since_hours * 3600 if since_hours else 0
    for line in p.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            epoch = e.get("epoch", 0)
            if epoch >= cutoff:
                events.append(e)
        except json.JSONDecodeError:
            continue
    return events


def compute_metrics(events):
    """从事件列表计算指标"""
    total = len(events)
    layer_counts = {l: 0 for l in LAYERS}
    ok_count = 0
    latencies = []

    for e in events:
        layer = e.get("layer", "?")
        if layer in layer_counts:
            layer_counts[layer] += 1
        if e.get("status") == "ok":
            ok_count += 1
        ms = e.get("latency_ms")
        if ms is not None and ms > 0:
            latencies.append(ms)

    tsr = ok_count / total if total > 0 else 1.0
    retry_count = sum(1 for e in events if e.get("payload", {}).get("retry", False))
    retry_rate = retry_count / total if total > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0

    layer_ratios = {}
    for l in LAYERS:
        layer_ratios[l] = layer_counts[l] / total if total > 0 else 0

    return {
        "total": total,
        "tsr": tsr,
        "retry_rate": retry_rate,
        "avg_latency_ms": round(avg_latency, 1),
        "p95_latency_ms": round(p95_latency, 1),
        "layer_counts": layer_counts,
        "layer_ratios": {k: round(v, 3) for k, v in layer_ratios.items()},
    }


def compare(recent, baseline):
    """对比两组指标，返回告警列表"""
    alerts = []

    # 1. 事件量偏差
    if baseline["total"] > 0:
        vol_pct = ((recent["total"] - baseline["total"]) / baseline["total"]) * 100
        if abs(vol_pct) > THRESHOLDS["event_volume_pct"]:
            direction = "偏高" if vol_pct > 0 else "偏低"
            alerts.append(
                {
                    "dim": "事件量",
                    "level": "WARN",
                    "msg": f"24h={recent['total']} vs 日均={baseline['total']:.0f}，{direction} {abs(vol_pct):.0f}%",
                }
            )

    # 2. TOOL 占比突增
    tool_diff = (
        recent["layer_ratios"].get("TOOL", 0) - baseline["layer_ratios"].get("TOOL", 0)
    ) * 100
    if tool_diff > THRESHOLDS["tool_ratio_spike_pct"]:
        alerts.append(
            {
                "dim": "结构占比",
                "level": "WARN",
                "msg": f"TOOL 占比 {recent['layer_ratios']['TOOL']*100:.0f}% → 突增 {tool_diff:.0f}%",
            }
        )

    # 3. TSR
    if recent["tsr"] < THRESHOLDS["tsr_min"]:
        alerts.append(
            {
                "dim": "成功质量",
                "level": "CRIT" if recent["tsr"] < 0.95 else "WARN",
                "msg": f"TSR={recent['tsr']*100:.1f}% (阈值 {THRESHOLDS['tsr_min']*100:.0f}%)",
            }
        )

    # 4. 时延上升
    if baseline["avg_latency_ms"] > 0:
        lat_pct = (
            (recent["avg_latency_ms"] - baseline["avg_latency_ms"])
            / baseline["avg_latency_ms"]
        ) * 100
        if lat_pct > THRESHOLDS["latency_spike_pct"]:
            alerts.append(
                {
                    "dim": "成功质量",
                    "level": "WARN",
                    "msg": f"平均时延 {recent['avg_latency_ms']}ms → 上升 {lat_pct:.0f}% (基线 {baseline['avg_latency_ms']}ms)",
                }
            )

    return alerts


def format_report(recent, baseline, alerts, fmt="markdown"):
    """生成报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    is_tg = fmt == "telegram"

    lines = []
    lines.append(f"{'📊' if is_tg else '##'} AIOS 趋势对比 | {now}")
    lines.append("")

    # 维度1: 事件量
    lines.append(f"{'📈' if is_tg else '###'} 事件量")
    lines.append(f"  24h: {recent['total']} | 7d日均: {baseline['total']:.1f}")
    if baseline["total"] > 0:
        pct = ((recent["total"] - baseline["total"]) / baseline["total"]) * 100
        lines.append(f"  偏差: {pct:+.0f}%")
    lines.append("")

    # 维度2: 结构占比
    lines.append(f"{'🏗️' if is_tg else '###'} 层分布 (24h vs 7d日均)")
    for l in LAYERS:
        r = recent["layer_ratios"].get(l, 0) * 100
        b = baseline["layer_ratios"].get(l, 0) * 100
        diff = r - b
        marker = " ⚠️" if abs(diff) > 20 else ""
        lines.append(f"  {l}: {r:.0f}% vs {b:.0f}% ({diff:+.0f}%){marker}")
    lines.append("")

    # 维度3: 成功质量
    lines.append(f"{'✅' if is_tg else '###'} 成功质量")
    lines.append(
        f"  TSR: {recent['tsr']*100:.1f}% | 重试率: {recent['retry_rate']*100:.1f}%"
    )
    lines.append(
        f"  平均时延: {recent['avg_latency_ms']}ms | P95: {recent['p95_latency_ms']}ms"
    )
    lines.append("")

    # 告警
    if alerts:
        lines.append(f"{'🚨' if is_tg else '###'} 超阈值告警")
        for a in alerts:
            icon = "🔴" if a["level"] == "CRIT" else "🟡"
            lines.append(f"  {icon} [{a['dim']}] {a['msg']}")
    else:
        lines.append("🟢 全部指标在阈值内")

    return "\n".join(lines)


def run(args=None):
    parser = argparse.ArgumentParser(description="AIOS 趋势对比")
    parser.add_argument("--save", action="store_true", help="保存报告")
    parser.add_argument(
        "--format", choices=["markdown", "telegram"], default="markdown"
    )
    opts = parser.parse_args(args)

    # 加载数据
    events_24h = load_events(since_hours=24)
    events_7d = load_events(since_hours=168)

    # 计算指标
    recent = compute_metrics(events_24h)

    # 7d 日均基线
    if events_7d:
        baseline_raw = compute_metrics(events_7d)
        # 计算实际天数跨度
        epochs = [e.get("epoch", 0) for e in events_7d if e.get("epoch")]
        if epochs:
            span_days = max((max(epochs) - min(epochs)) / 86400, 1)
        else:
            span_days = 7
        # 日均化
        baseline = {
            "total": baseline_raw["total"] / span_days,
            "tsr": baseline_raw["tsr"],
            "retry_rate": baseline_raw["retry_rate"],
            "avg_latency_ms": baseline_raw["avg_latency_ms"],
            "p95_latency_ms": baseline_raw["p95_latency_ms"],
            "layer_counts": {
                k: v / span_days for k, v in baseline_raw["layer_counts"].items()
            },
            "layer_ratios": baseline_raw["layer_ratios"],
        }
    else:
        baseline = recent  # 无历史数据，用自身

    # 对比
    alerts = compare(recent, baseline)

    # 输出
    report = format_report(recent, baseline, alerts, fmt=opts.format)
    print(report)

    # 保存
    if opts.save:
        reports_dir = Path(__file__).resolve().parent.parent / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        out = reports_dir / f"trend_{ts}.md"
        out.write_text(report, encoding="utf-8")
        print(f"\n💾 已保存: {out}")

    # 返回是否有告警（供外部调用）
    return len(alerts) > 0, alerts


if __name__ == "__main__":
    run()
