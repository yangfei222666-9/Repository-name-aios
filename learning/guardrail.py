# aios/learning/guardrail.py - 门禁：进化不能倒退
"""
规则（最小可行）：
  - correction_rate 连续 3 次上升 → L2 ticket
  - tool_success_rate 连续 2 次下降 → L2 ticket
  - 某 tool p95_ms 连续 3 次上升 → L2 ticket

先报警不自动修，保证安全。
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class Ticket:
    level: str
    title: str
    evidence: dict[str, Any]


def _getv(d: dict, path: str, default=None):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _is_increasing(seq: list[float]) -> bool:
    return all(seq[i] < seq[i + 1] for i in range(len(seq) - 1))


def _is_decreasing(seq: list[float]) -> bool:
    return all(seq[i] > seq[i + 1] for i in range(len(seq) - 1))


def guardrail_from_history(history: list[dict]) -> list[Ticket]:
    """从 baseline history 检测退化"""
    tickets: list[Ticket] = []

    if len(history) < 4:
        return tickets

    # 规则 1: correction_rate 连续 3 次上升
    cr = [float(_getv(x, "correction_rate", 0.0)) for x in history[-4:]]
    if _is_increasing(cr[-3:]):
        tickets.append(
            Ticket(
                level="L2",
                title="correction_rate increasing 3x",
                evidence={"last4": cr, "rule": "correction_rate up 3x"},
            )
        )

    # 规则 2: tool_success_rate 连续 2 次下降
    ts = [float(_getv(x, "tool_success_rate", 0.0)) for x in history[-3:]]
    if _is_decreasing(ts[-2:]):
        tickets.append(
            Ticket(
                level="L2",
                title="tool_success_rate decreasing 2x",
                evidence={"last3": ts, "rule": "tool_success_rate down 2x"},
            )
        )

    # 规则 3: 某 tool p95 连续 3 次上升
    last4 = history[-4:]
    tool_keys = set()
    for x in last4:
        tool_p95 = _getv(x, "tool_p95_ms", {}) or {}
        tool_keys |= set(tool_p95.keys())

    for tool in sorted(tool_keys):
        seq = []
        for x in last4:
            tool_p95 = _getv(x, "tool_p95_ms", {}) or {}
            v = tool_p95.get(tool)
            if v is None:
                seq = []
                break
            seq.append(float(v))
        if len(seq) == 4 and _is_increasing(seq[-3:]):
            tickets.append(
                Ticket(
                    level="L2",
                    title=f"p95 rising 3x: {tool}",
                    evidence={
                        "tool": tool,
                        "last4_p95_ms": seq,
                        "rule": "p95_ms up 3x",
                    },
                )
            )

    return tickets


def run_guardrail(history: list[dict]) -> dict:
    """运行门禁，返回结构化结果"""
    alerts = guardrail_from_history(history)
    return {
        "alerts": [asdict(t) for t in alerts],
        "status": "regression_detected" if alerts else "gate_passed",
        "snapshots": len(history),
    }
