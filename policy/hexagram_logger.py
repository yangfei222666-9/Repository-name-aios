"""
Hexagram Logger v2.0 - 工程级卦象状态记录

新增字段（2026-03-05）：
- system_load: 组合负载指标（low/normal/high）
- load_score: 归一化负载分数（0-1）
- task_volume: 任务到达率（low/normal/high）
- tasks_per_min: 每分钟任务数
- pending_tasks: 当前待处理任务数
- runtime_phase: 运行阶段（stable/pressure/recovery）
- state_duration: 当前卦象持续时间（秒）
- transition_type: 转换类型（normal/stress/recovery）
- latency_baseline: 动态基线（最近100次中位数）
- latency_pressure: 延迟压力比（avg/baseline）
- latency_state: 延迟状态（normal/elevated/high）
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from collections import deque

# 数据文件路径
HEXAGRAM_HISTORY_FILE = Path(__file__).parent.parent / "data" / "hexagram_history.jsonl"

# 延迟历史（用于动态 baseline）
_latency_window = deque(maxlen=100)

# 上一次卦象状态（用于计算 state_duration 和 transition_type）
_last_hexagram = None
_last_hexagram_time = None


def _compute_load_score(
    cpu_usage: float = 0.0,
    memory_usage: float = 0.0,
    pending_tasks: int = 0,
    max_queue: int = 50,
    avg_latency: float = 0.0,
    latency_baseline: float = 10.0
) -> tuple[float, str]:
    """计算组合负载分数"""
    queue_utilization = min(pending_tasks / max(max_queue, 1), 1.0)
    latency_pressure = avg_latency / max(latency_baseline, 0.1)
    latency_pressure_capped = min(latency_pressure, 3.0) / 3.0  # 归一化到 0-1

    load_score = (
        cpu_usage * 0.3 +
        memory_usage * 0.2 +
        queue_utilization * 0.3 +
        latency_pressure_capped * 0.2
    )
    load_score = round(min(load_score, 1.0), 4)

    if load_score < 0.4:
        system_load = "low"
    elif load_score < 0.7:
        system_load = "normal"
    else:
        system_load = "high"

    return load_score, system_load


def _compute_latency_baseline(current_latency: float) -> float:
    """动态 baseline：最近 100 次延迟的中位数"""
    _latency_window.append(current_latency)
    if len(_latency_window) < 3:
        return current_latency  # 数据不足时用当前值
    return round(statistics.median(_latency_window), 2)


def _compute_latency_pressure(avg_latency: float, baseline: float) -> tuple[float, str]:
    """计算延迟压力"""
    pressure = round(avg_latency / max(baseline, 0.1), 2)
    if pressure < 1.2:
        state = "normal"
    elif pressure < 1.8:
        state = "elevated"
    else:
        state = "high"
    return pressure, state


def _compute_task_volume(tasks_last_5min: int) -> tuple[float, str]:
    """计算任务到达率"""
    tasks_per_min = round(tasks_last_5min / 5.0, 2)
    if tasks_per_min < 2:
        volume = "low"
    elif tasks_per_min < 10:
        volume = "normal"
    else:
        volume = "high"
    return tasks_per_min, volume


def _compute_runtime_phase(success_rate: float) -> str:
    """计算运行阶段"""
    if success_rate >= 0.95:
        return "stable"
    elif success_rate >= 0.90:
        return "pressure"
    else:
        return "recovery"


def _compute_transition_type(from_hex: str, to_hex: str, success_rate: float) -> str:
    """判断转换类型"""
    if from_hex is None or from_hex == to_hex:
        return "normal"
    if success_rate < 0.90:
        return "stress"
    # 已知恢复路径（坎→复 等）
    recovery_pairs = {("坎", "复"), ("离", "坤"), ("震", "坤"), ("大过", "坤")}
    if (from_hex, to_hex) in recovery_pairs:
        return "recovery"
    return "normal"


def _compute_state_duration(current_hexagram: str) -> int:
    """计算当前卦象持续时间（秒）"""
    global _last_hexagram, _last_hexagram_time
    now = datetime.now()

    if _last_hexagram != current_hexagram:
        _last_hexagram = current_hexagram
        _last_hexagram_time = now
        return 0

    if _last_hexagram_time is None:
        _last_hexagram_time = now
        return 0

    return int((now - _last_hexagram_time).total_seconds())


def append_hexagram_state(
    trigram_upper: str,
    trigram_lower: str,
    hexagram: str,
    success_rate: float,
    latency: float,
    debate_rate: float,
    # 新增可选参数
    cpu_usage: float = 0.0,
    memory_usage: float = 0.0,
    pending_tasks: int = 0,
    tasks_last_5min: int = 0,
    max_queue: int = 50,
    hexagram_number: int = 0,
    metrics: dict = None
):
    """
    记录卦象状态到历史文件（工程级 v2.0）

    Args:
        trigram_upper: 上卦（如"坎"）
        trigram_lower: 下卦（如"坤"）
        hexagram: 卦象名称（如"水地比"）
        success_rate: 成功率（0-1）
        latency: 平均延迟（秒）
        debate_rate: 辩论率（0-1）
        cpu_usage: CPU 使用率（0-1）
        memory_usage: 内存使用率（0-1）
        pending_tasks: 当前待处理任务数
        tasks_last_5min: 最近 5 分钟任务数
        max_queue: 队列最大容量
        hexagram_number: 卦象编号（1-64）
        metrics: 原始指标（可选）
    """
    HEXAGRAM_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 动态 baseline
    latency_baseline = _compute_latency_baseline(latency)
    latency_pressure, latency_state = _compute_latency_pressure(latency, latency_baseline)

    # 组合负载
    load_score, system_load = _compute_load_score(
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        pending_tasks=pending_tasks,
        max_queue=max_queue,
        avg_latency=latency,
        latency_baseline=latency_baseline
    )

    # 任务量
    tasks_per_min, task_volume = _compute_task_volume(tasks_last_5min)

    # 运行阶段
    runtime_phase = _compute_runtime_phase(success_rate)

    # 状态持续时间
    state_duration = _compute_state_duration(hexagram)

    # 转换类型（需要读取上一条记录）
    prev_hexagram = _get_last_hexagram_name()
    transition_type = _compute_transition_type(prev_hexagram, hexagram, success_rate)

    record = {
        "timestamp": datetime.now().isoformat(),
        "trigram_upper": trigram_upper,
        "trigram_lower": trigram_lower,
        "hexagram": hexagram,
        "hexagram_number": hexagram_number,
        "success_rate": round(success_rate, 4),
        "avg_latency": round(latency, 2),
        "latency_baseline": latency_baseline,
        "latency_pressure": latency_pressure,
        "latency_state": latency_state,
        "debate_rate": round(debate_rate, 4),
        "system_load": system_load,
        "load_score": load_score,
        "task_volume": task_volume,
        "tasks_per_min": tasks_per_min,
        "pending_tasks": pending_tasks,
        "runtime_phase": runtime_phase,
        "state_duration": state_duration,
        "transition_type": transition_type
    }

    if metrics:
        record["metrics"] = metrics

    with open(HEXAGRAM_HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def _get_last_hexagram_name() -> str | None:
    """读取上一条记录的卦象名"""
    if not HEXAGRAM_HISTORY_FILE.exists():
        return None
    last = None
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = json.loads(line).get("hexagram")
    return last


def get_recent_hexagrams(limit: int = 10):
    """获取最近的卦象序列"""
    if not HEXAGRAM_HISTORY_FILE.exists():
        return []
    records = []
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records[-limit:][::-1]


def get_hexagram_timeline(days: int = 7):
    """获取卦象时间线（按天聚合）"""
    if not HEXAGRAM_HISTORY_FILE.exists():
        return []

    from collections import defaultdict, Counter

    daily_hexagrams = defaultdict(list)
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                date = record["timestamp"][:10]
                daily_hexagrams[date].append(record["hexagram"])

    timeline = []
    for date in sorted(daily_hexagrams.keys())[-days:]:
        hexagrams = daily_hexagrams[date]
        most_common = Counter(hexagrams).most_common(1)[0]
        timeline.append({
            "date": date,
            "hexagram": most_common[0],
            "count": most_common[1],
            "total": len(hexagrams)
        })
    return timeline


def analyze_transitions(min_count: int = 1):
    """分析卦象转移频率"""
    if not HEXAGRAM_HISTORY_FILE.exists():
        return []

    from collections import Counter

    hexagrams = []
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                hexagrams.append(json.loads(line)["hexagram"])

    transitions = [(hexagrams[i], hexagrams[i+1]) for i in range(len(hexagrams)-1)]
    counts = Counter(transitions)
    return [
        {"from": f, "to": t, "count": c}
        for (f, t), c in counts.most_common()
        if c >= min_count
    ]


def compute_stability_index() -> dict:
    """
    计算 System Stability Index

    stability = 0.4 * (1 - transition_entropy) + 0.3 * success_rate + 0.3 * (1 / latency_pressure)
    """
    import math
    from collections import Counter

    if not HEXAGRAM_HISTORY_FILE.exists():
        return {"stability": 0.0, "transition_entropy": 0.0, "distribution_entropy": 0.0}

    records = []
    with open(HEXAGRAM_HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if len(records) < 2:
        return {"stability": 1.0, "transition_entropy": 0.0, "distribution_entropy": 0.0}

    hexagrams = [r["hexagram"] for r in records]

    # Transition Entropy
    transitions = [(hexagrams[i], hexagrams[i+1]) for i in range(len(hexagrams)-1)]
    trans_counts = Counter(transitions)
    total_trans = len(transitions)
    trans_entropy = -sum(
        (c/total_trans) * math.log2(c/total_trans)
        for c in trans_counts.values()
    ) if total_trans > 0 else 0.0
    # 归一化（最大熵 = log2(N)）
    max_entropy = math.log2(max(len(trans_counts), 1))
    norm_trans_entropy = trans_entropy / max(max_entropy, 1)

    # Distribution Entropy
    hex_counts = Counter(hexagrams)
    total_hex = len(hexagrams)
    dist_entropy = -sum(
        (c/total_hex) * math.log2(c/total_hex)
        for c in hex_counts.values()
    ) if total_hex > 0 else 0.0
    max_dist_entropy = math.log2(max(len(hex_counts), 1))
    norm_dist_entropy = dist_entropy / max(max_dist_entropy, 1)

    # 最近指标
    recent = records[-10:]
    avg_success = sum(r.get("success_rate", 0.9) for r in recent) / len(recent)
    avg_pressure = sum(r.get("latency_pressure", 1.0) for r in recent) / len(recent)

    stability = (
        0.4 * (1 - norm_trans_entropy) +
        0.3 * avg_success +
        0.3 * (1 / max(avg_pressure, 0.1))
    )
    stability = round(min(stability, 1.0), 4)

    return {
        "stability": stability,
        "stability_pct": round(stability * 100, 1),
        "transition_entropy": round(norm_trans_entropy, 4),
        "distribution_entropy": round(norm_dist_entropy, 4),
        "avg_success_rate": round(avg_success, 4),
        "avg_latency_pressure": round(avg_pressure, 4)
    }


if __name__ == "__main__":
    print("Hexagram Logger v2.0 Demo")
    print("=" * 60)

    record = append_hexagram_state(
        trigram_upper="坎",
        trigram_lower="坤",
        hexagram="水地比",
        success_rate=0.91,
        latency=12.3,
        debate_rate=0.27,
        cpu_usage=0.65,
        memory_usage=0.55,
        pending_tasks=8,
        tasks_last_5min=30
    )
    print(f"✅ Logged: {record['hexagram']} @ {record['timestamp'][:19]}")
    print(f"   system_load={record['system_load']} load_score={record['load_score']}")
    print(f"   task_volume={record['task_volume']} tasks_per_min={record['tasks_per_min']}")
    print(f"   runtime_phase={record['runtime_phase']}")
    print(f"   latency_baseline={record['latency_baseline']} pressure={record['latency_pressure']} ({record['latency_state']})")
    print(f"   state_duration={record['state_duration']}s transition_type={record['transition_type']}")

    print("\n📊 System Stability Index:")
    si = compute_stability_index()
    print(f"   Stability: {si['stability_pct']}%")
    print(f"   Transition Entropy: {si['transition_entropy']}")
    print(f"   Distribution Entropy: {si['distribution_entropy']}")

    print("\n卦象时间线（最近 7 天）：")
    for t in get_hexagram_timeline(days=7):
        print(f"  {t['date']} | {t['hexagram']} ({t['count']}/{t['total']})")

    print("\n卦象转移（Top 5）：")
    for tr in analyze_transitions()[:5]:
        print(f"  {tr['from']} → {tr['to']} ({tr['count']}次)")
