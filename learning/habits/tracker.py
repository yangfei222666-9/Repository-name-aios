"""
aios/learning/habits/tracker.py - 个人习惯数据收集器

功能：
1. 监听 AppMonitor 事件，记录应用使用
2. 生成每日汇总报告
3. 提供查询接口

数据格式：
- app_usage.jsonl: 应用使用记录（追加写入）
- daily_summary.jsonl: 每日汇总（每天一条）
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data"
APP_USAGE_FILE = DATA_DIR / "app_usage.jsonl"
DAILY_SUMMARY_FILE = DATA_DIR / "daily_summary.jsonl"
STATE_FILE = DATA_DIR / "tracker_state.json"


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
    return {
        "app_sessions": {},  # {app_name: start_timestamp}
        "last_summary_date": None,
    }


def _save_state(state: dict):
    """保存追踪器状态"""
    _ensure_data_dir()
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _append_usage(record: dict):
    """追加应用使用记录"""
    _ensure_data_dir()
    with open(APP_USAGE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _append_summary(summary: dict):
    """追加每日汇总"""
    _ensure_data_dir()
    with open(DAILY_SUMMARY_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False) + "\n")


def track_app_event(app: str, action: str, timestamp: Optional[float] = None):
    """
    记录应用事件

    Args:
        app: 应用名称
        action: 动作类型（started/stopped）
        timestamp: 时间戳（默认当前时间）
    """
    if timestamp is None:
        timestamp = time.time()

    dt = datetime.fromtimestamp(timestamp)
    state = _load_state()

    record = {
        "timestamp": timestamp,
        "app": app,
        "action": action,
        "hour": dt.hour,
        "weekday": dt.weekday(),
        "is_weekend": dt.weekday() >= 5,
    }

    if action == "started":
        # 记录启动时间
        state["app_sessions"][app] = timestamp
        _append_usage(record)

    elif action == "stopped":
        # 计算使用时长
        start_time = state["app_sessions"].get(app)
        if start_time:
            duration = int(timestamp - start_time)
            record["duration_sec"] = duration
            del state["app_sessions"][app]
        _append_usage(record)

    _save_state(state)


def generate_daily_summary(date: Optional[str] = None) -> dict:
    """
    生成每日汇总

    Args:
        date: 日期字符串（YYYY-MM-DD），默认昨天

    Returns:
        每日汇总字典
    """
    if date is None:
        yesterday = datetime.now() - timedelta(days=1)
        date = yesterday.strftime("%Y-%m-%d")

    if not APP_USAGE_FILE.exists():
        return {}

    # 读取当天的所有记录
    target_date = datetime.strptime(date, "%Y-%m-%d")
    start_ts = target_date.timestamp()
    end_ts = (target_date + timedelta(days=1)).timestamp()

    apps = {}
    hourly_activity = [0] * 24

    with open(APP_USAGE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                ts = record["timestamp"]

                if start_ts <= ts < end_ts:
                    app = record["app"]
                    action = record["action"]
                    hour = record["hour"]

                    if app not in apps:
                        apps[app] = {"duration": 0, "sessions": 0}

                    if action == "started":
                        apps[app]["sessions"] += 1

                    if action == "stopped" and "duration_sec" in record:
                        apps[app]["duration"] += record["duration_sec"]
                        hourly_activity[hour] += 1
            except Exception:
                continue

    # 识别活跃时段（有活动的小时）
    peak_hours = [h for h, count in enumerate(hourly_activity) if count > 0]

    # 分类活动类型（简单规则）
    activity_type = {}
    for app, stats in apps.items():
        if "LOL" in app or "WeGame" in app:
            activity_type["gaming"] = activity_type.get("gaming", 0) + stats["duration"]
        elif "QQ音乐" in app or "Music" in app:
            activity_type["music"] = activity_type.get("music", 0) + stats["duration"]
        else:
            activity_type["other"] = activity_type.get("other", 0) + stats["duration"]

    summary = {
        "date": date,
        "weekday": target_date.weekday(),
        "apps": apps,
        "peak_hours": peak_hours,
        "activity_type": activity_type,
        "total_active_hours": len(peak_hours),
    }

    _append_summary(summary)

    # 更新状态
    state = _load_state()
    state["last_summary_date"] = date
    _save_state(state)

    return summary


def get_recent_summaries(days: int = 7) -> list[dict]:
    """
    获取最近 N 天的汇总

    Args:
        days: 天数

    Returns:
        汇总列表
    """
    if not DAILY_SUMMARY_FILE.exists():
        return []

    summaries = []
    with open(DAILY_SUMMARY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                summary = json.loads(line.strip())
                summaries.append(summary)
            except Exception:
                continue

    # 返回最近 N 天
    return summaries[-days:] if len(summaries) > days else summaries


def get_app_stats(app: str, days: int = 7) -> dict:
    """
    获取某个应用的统计数据

    Args:
        app: 应用名称
        days: 统计天数

    Returns:
        统计字典
    """
    summaries = get_recent_summaries(days)

    total_duration = 0
    total_sessions = 0
    daily_usage = []

    for summary in summaries:
        if app in summary.get("apps", {}):
            stats = summary["apps"][app]
            total_duration += stats["duration"]
            total_sessions += stats["sessions"]
            daily_usage.append(
                {
                    "date": summary["date"],
                    "duration": stats["duration"],
                    "sessions": stats["sessions"],
                }
            )

    return {
        "app": app,
        "days": days,
        "total_duration": total_duration,
        "total_sessions": total_sessions,
        "avg_duration_per_day": total_duration / days if days > 0 else 0,
        "avg_sessions_per_day": total_sessions / days if days > 0 else 0,
        "daily_usage": daily_usage,
    }


def check_and_generate_summary():
    """
    检查是否需要生成昨天的汇总

    每天第一次运行时自动生成昨天的汇总
    """
    state = _load_state()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if state.get("last_summary_date") != yesterday:
        summary = generate_daily_summary(yesterday)
        return summary

    return None


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "summary":
            # 生成昨天的汇总
            summary = generate_daily_summary()
            print(json.dumps(summary, ensure_ascii=False, indent=2))

        elif cmd == "stats":
            # 查看应用统计
            app = sys.argv[2] if len(sys.argv) > 2 else "LOL"
            stats = get_app_stats(app, days=7)
            print(json.dumps(stats, ensure_ascii=False, indent=2))

        elif cmd == "recent":
            # 查看最近汇总
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            summaries = get_recent_summaries(days)
            print(json.dumps(summaries, ensure_ascii=False, indent=2))

    else:
        print("Usage:")
        print("  python tracker.py summary          # 生成昨天的汇总")
        print("  python tracker.py stats [app]      # 查看应用统计")
        print("  python tracker.py recent [days]    # 查看最近汇总")
