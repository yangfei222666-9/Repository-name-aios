"""
aios/learning/feedback/tracker.py - 反馈追踪器

功能：
1. 记录用户反馈（显式 + 隐式）
2. 关联反馈到具体行动
3. 提供查询接口

反馈类型：
- explicit: 用户主动给的反馈
- implicit: 系统推断的反馈
"""

import json
import time
import re
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).resolve().parent / "data"
FEEDBACK_FILE = DATA_DIR / "feedback.jsonl"
STATS_FILE = DATA_DIR / "feedback_stats.json"
STATE_FILE = DATA_DIR / "tracker_state.json"

# 反馈关键词
POSITIVE_KEYWORDS = [
    "有用",
    "好",
    "不错",
    "可以",
    "行",
    "👍",
    "赞",
    "很好",
    "完美",
    "太棒",
    "excellent",
    "good",
    "useful",
]

NEGATIVE_KEYWORDS = [
    "没用",
    "不好",
    "别",
    "不要",
    "👎",
    "差",
    "烦",
    "吵",
    "不需要",
    "useless",
    "bad",
    "annoying",
]


def _ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_state() -> dict:
    """加载追踪器状态"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"recent_actions": [], "last_feedback_id": 0}  # 最近的行动，用于关联反馈


def _save_state(state: dict):
    """保存追踪器状态"""
    _ensure_data_dir()
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _append_feedback(record: dict):
    """追加反馈记录"""
    _ensure_data_dir()
    with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _generate_feedback_id() -> str:
    """生成反馈 ID"""
    state = _load_state()
    state["last_feedback_id"] += 1
    _save_state(state)
    date_str = datetime.now().strftime("%Y%m%d")
    return f"fb-{date_str}-{state['last_feedback_id']:03d}"


def detect_feedback_in_message(
    message: str,
) -> Optional[Literal["useful", "not_useful"]]:
    """
    从用户消息中检测反馈关键词

    Args:
        message: 用户消息

    Returns:
        "useful" / "not_useful" / None
    """
    message_lower = message.lower()

    # 检测正面反馈
    for kw in POSITIVE_KEYWORDS:
        if kw in message_lower:
            return "useful"

    # 检测负面反馈
    for kw in NEGATIVE_KEYWORDS:
        if kw in message_lower:
            return "not_useful"

    return None


def record_feedback(
    value: Literal["useful", "not_useful", "very_useful"],
    feedback_type: Literal["explicit", "implicit"] = "explicit",
    action_id: Optional[str] = None,
    action_type: Optional[str] = None,
    category: Optional[str] = None,
    message: Optional[str] = None,
    user_comment: Optional[str] = None,
    timestamp: Optional[float] = None,
) -> str:
    """
    记录一条反馈

    Args:
        value: 反馈值（useful/not_useful/very_useful）
        feedback_type: 反馈类型（explicit/implicit）
        action_id: 关联的行动 ID
        action_type: 行动类型（suggestion/reminder/alert）
        category: 类别（habit_suggestion/health_reminder 等）
        message: 行动的具体消息
        user_comment: 用户评论
        timestamp: 时间戳（默认当前时间）

    Returns:
        feedback_id
    """
    if timestamp is None:
        timestamp = time.time()

    feedback_id = _generate_feedback_id()

    record = {
        "timestamp": timestamp,
        "feedback_id": feedback_id,
        "type": feedback_type,
        "value": value,
        "context": {
            "action_type": action_type,
            "action_id": action_id,
            "message": message,
            "category": category,
        },
        "user_comment": user_comment,
    }

    _append_feedback(record)
    return feedback_id


def record_action(
    action_id: str,
    action_type: str,
    category: str,
    message: str,
    timestamp: Optional[float] = None,
):
    """
    记录一个行动（用于后续关联反馈）

    Args:
        action_id: 行动 ID
        action_type: 行动类型
        category: 类别
        message: 消息内容
        timestamp: 时间戳
    """
    if timestamp is None:
        timestamp = time.time()

    state = _load_state()

    # 保留最近 10 个行动
    state["recent_actions"].append(
        {
            "action_id": action_id,
            "action_type": action_type,
            "category": category,
            "message": message,
            "timestamp": timestamp,
        }
    )

    if len(state["recent_actions"]) > 10:
        state["recent_actions"] = state["recent_actions"][-10:]

    _save_state(state)


def get_recent_action() -> Optional[dict]:
    """获取最近的一个行动"""
    state = _load_state()
    if state["recent_actions"]:
        return state["recent_actions"][-1]
    return None


def auto_associate_feedback(
    value: Literal["useful", "not_useful"],
    user_message: str,
    timestamp: Optional[float] = None,
) -> Optional[str]:
    """
    自动关联反馈到最近的行动

    Args:
        value: 反馈值
        user_message: 用户消息（用于提取评论）
        timestamp: 时间戳

    Returns:
        feedback_id or None
    """
    recent_action = get_recent_action()

    if not recent_action:
        return None

    # 检查时间间隔（5 分钟内）
    if timestamp is None:
        timestamp = time.time()

    time_diff = timestamp - recent_action["timestamp"]
    if time_diff > 300:  # 5 分钟
        return None

    # 记录反馈
    feedback_id = record_feedback(
        value=value,
        feedback_type="explicit",
        action_id=recent_action["action_id"],
        action_type=recent_action["action_type"],
        category=recent_action["category"],
        message=recent_action["message"],
        user_comment=user_message if len(user_message) < 200 else None,
        timestamp=timestamp,
    )

    return feedback_id


def get_feedback_stats(days: int = 7) -> dict:
    """
    获取反馈统计

    Args:
        days: 统计天数

    Returns:
        统计字典
    """
    if not FEEDBACK_FILE.exists():
        return {
            "total": 0,
            "by_value": {},
            "by_category": {},
            "by_action_type": {},
            "acceptance_rate": 0,
        }

    cutoff = time.time() - (days * 86400)

    total = 0
    by_value = {}
    by_category = {}
    by_action_type = {}

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                ts = record["timestamp"]

                if ts < cutoff:
                    continue

                total += 1
                value = record["value"]
                category = record["context"].get("category", "unknown")
                action_type = record["context"].get("action_type", "unknown")

                by_value[value] = by_value.get(value, 0) + 1

                if category not in by_category:
                    by_category[category] = {"useful": 0, "not_useful": 0}
                if value in ("useful", "very_useful"):
                    by_category[category]["useful"] += 1
                else:
                    by_category[category]["not_useful"] += 1

                if action_type not in by_action_type:
                    by_action_type[action_type] = {"useful": 0, "not_useful": 0}
                if value in ("useful", "very_useful"):
                    by_action_type[action_type]["useful"] += 1
                else:
                    by_action_type[action_type]["not_useful"] += 1

            except Exception:
                continue

    # 计算接受率
    useful_count = by_value.get("useful", 0) + by_value.get("very_useful", 0)
    acceptance_rate = useful_count / total if total > 0 else 0

    return {
        "total": total,
        "days": days,
        "by_value": by_value,
        "by_category": by_category,
        "by_action_type": by_action_type,
        "acceptance_rate": round(acceptance_rate, 2),
    }


def generate_stats_report(days: int = 7) -> str:
    """
    生成反馈统计报告（文本格式）

    Args:
        days: 统计天数

    Returns:
        报告文本
    """
    stats = get_feedback_stats(days)

    if stats["total"] == 0:
        return f"📊 反馈统计（最近 {days} 天）\n\n暂无反馈数据"

    lines = [
        f"📊 反馈统计（最近 {days} 天）",
        f"",
        f"总反馈数：{stats['total']}",
        f"接受率：{stats['acceptance_rate'] * 100:.0f}%",
        f"",
    ]

    # 按类别统计
    if stats["by_category"]:
        lines.append("按类别：")
        for cat, counts in stats["by_category"].items():
            total_cat = counts["useful"] + counts["not_useful"]
            rate = counts["useful"] / total_cat if total_cat > 0 else 0
            lines.append(f"  {cat}: {counts['useful']}/{total_cat} ({rate*100:.0f}%)")
        lines.append("")

    # 按行动类型统计
    if stats["by_action_type"]:
        lines.append("按行动类型：")
        for atype, counts in stats["by_action_type"].items():
            total_type = counts["useful"] + counts["not_useful"]
            rate = counts["useful"] / total_type if total_type > 0 else 0
            lines.append(
                f"  {atype}: {counts['useful']}/{total_type} ({rate*100:.0f}%)"
            )

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "stats":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            print(generate_stats_report(days))

        elif cmd == "test":
            # 测试记录反馈
            record_action(
                action_id="test-001",
                action_type="suggestion",
                category="habit_suggestion",
                message="测试建议",
            )

            feedback_id = record_feedback(
                value="useful",
                feedback_type="explicit",
                action_id="test-001",
                action_type="suggestion",
                category="habit_suggestion",
                message="测试建议",
            )

            print(f"记录反馈成功：{feedback_id}")
            print(generate_stats_report(7))

    else:
        print("Usage:")
        print("  python tracker.py stats [days]  # 查看统计")
        print("  python tracker.py test          # 测试记录")
