#!/usr/bin/env python3
"""清理 AIOS 超过指定天数的旧事件日志。

用法:
    python cleanup_old_events.py                        # 清理 >7 天的事件
    python cleanup_old_events.py --days 14              # 清理 >14 天的事件
    python cleanup_old_events.py --dry-run              # 预览，不实际删除
    python cleanup_old_events.py --file path/to/events.jsonl
"""

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("cleanup_old_events")

# 默认 events.jsonl 位置（脚本所在目录的上两级，即 aios/）
DEFAULT_EVENTS_PATH = Path(__file__).resolve().parent.parent / "events.jsonl"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="清理 AIOS 旧事件日志")
    p.add_argument(
        "--days",
        type=int,
        default=7,
        help="保留最近 N 天的事件（默认 7）",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览，不实际修改文件",
    )
    p.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_EVENTS_PATH,
        help=f"events.jsonl 路径（默认 {DEFAULT_EVENTS_PATH}）",
    )
    return p.parse_args()


def _parse_timestamp(event: dict) -> datetime | None:
    """从事件中提取时间戳，支持多种常见字段名和格式。"""
    for key in ("timestamp", "ts", "time", "created_at", "date"):
        val = event.get(key)
        if val is None:
            continue
        # Unix 秒 / 毫秒
        if isinstance(val, (int, float)):
            ts = val if val < 1e12 else val / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        # ISO 8601 字符串
        if isinstance(val, str):
            for fmt in (
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
            ):
                try:
                    dt = datetime.strptime(val, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
    return None


def cleanup(events_path: Path, days: int, dry_run: bool) -> dict:
    """执行清理，返回报告字典。"""
    if not events_path.exists():
        log.error("文件不存在: %s", events_path)
        sys.exit(1)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    log.info("截止时间: %s（保留此时间之后的事件）", cutoff.isoformat())

    kept: list[str] = []
    removed = 0
    skipped = 0
    errors = 0
    total = 0

    with open(events_path, "r", encoding="utf-8") as f:
        for lineno, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue
            total += 1
            try:
                event = json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("第 %d 行 JSON 解析失败: %s", lineno, e)
                errors += 1
                kept.append(raw_line)  # 保留无法解析的行，避免数据丢失
                continue

            ts = _parse_timestamp(event)
            if ts is None:
                log.debug("第 %d 行无时间戳，保留", lineno)
                skipped += 1
                kept.append(raw_line)
                continue

            if ts >= cutoff:
                kept.append(raw_line)
            else:
                removed += 1

    report = {
        "file": str(events_path),
        "days": days,
        "cutoff": cutoff.isoformat(),
        "total": total,
        "kept": total - removed,
        "removed": removed,
        "skipped_no_ts": skipped,
        "parse_errors": errors,
        "dry_run": dry_run,
    }

    if dry_run:
        log.info("[DRY-RUN] 不修改文件")
    else:
        # 原子写入：先写临时文件，再替换
        dir_ = events_path.parent
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.writelines(kept)
            # Windows 上 rename 需要先删目标
            backup = events_path.with_suffix(".jsonl.bak")
            shutil.copy2(events_path, backup)
            os.replace(tmp_path, events_path)
            log.info("已备份原文件至 %s", backup)
        except OSError as e:
            log.error("写入失败: %s", e)
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            sys.exit(1)

    return report


def print_report(report: dict) -> None:
    log.info("=" * 40)
    log.info("清理报告")
    log.info("=" * 40)
    log.info("文件:        %s", report["file"])
    log.info("保留天数:    %d", report["days"])
    log.info("截止时间:    %s", report["cutoff"])
    log.info("总事件数:    %d", report["total"])
    log.info("保留:        %d", report["kept"])
    log.info("删除:        %d", report["removed"])
    if report["skipped_no_ts"]:
        log.info("无时间戳(保留): %d", report["skipped_no_ts"])
    if report["parse_errors"]:
        log.warning("解析错误(保留): %d", report["parse_errors"])
    if report["dry_run"]:
        log.info("模式:        DRY-RUN（未修改文件）")
    else:
        log.info("模式:        已执行清理")
    log.info("=" * 40)


def main() -> None:
    args = parse_args()
    if args.days < 0:
        log.error("--days 不能为负数")
        sys.exit(1)

    log.info("开始清理 %s（保留 %d 天）%s", args.file, args.days, " [DRY-RUN]" if args.dry_run else "")
    report = cleanup(args.file, args.days, args.dry_run)
    print_report(report)


if __name__ == "__main__":
    main()
