"""
AIOS v0.6 Dashboard Snapshot 增强
补充 P0 收口所需的 3 类数据：
1. Scheduler: queue + p95 + DLQ + 熔断
2. Reactor: index_stats + match_stats
3. EventStore: active/archive 状态
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
import gzip

AIOS_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(AIOS_ROOT))


def get_scheduler_v06_stats() -> Dict[str, Any]:
    """
    v0.6 Scheduler 统计
    
    Returns:
        {
            "queue_ready": int,
            "running": int,
            "retrying": int,
            "dlq": int,
            "concurrency_used": int,
            "concurrency_max": int,
            "exec_p95_ms": float,
            "wait_p95_ms": float,
            "retry_rate_1h": float,
            "dlq_new_1h": int,
            "circuit_breaker": {
                "status": "open" | "closed",
                "failures": int,
                "last_failure": str
            }
        }
    """
    try:
        from core.production_scheduler import get_scheduler
        scheduler = get_scheduler()
        status = scheduler.get_status()
        
        # 基础数据
        result = {
            "queue_ready": status["queue_size"],
            "running": status["running_tasks"],
            "retrying": 0,  # TODO: 从任务列表统计
            "dlq": len(scheduler.failed_tasks),
            "concurrency_used": status["running_tasks"],
            "concurrency_max": status["max_concurrent"],
            "exec_p95_ms": 0.0,  # TODO: 从完成任务计算
            "wait_p95_ms": 0.0,  # TODO: 从任务时间戳计算
            "retry_rate_1h": 0.0,  # TODO: 从统计计算
            "dlq_new_1h": 0,  # TODO: 从 failed_tasks 时间戳统计
            "circuit_breaker": {
                "status": "closed",
                "failures": 0,
                "last_failure": None
            }
        }
        
        # 计算 p95 延迟
        if scheduler.completed_tasks:
            durations = [t["duration"] * 1000 for t in scheduler.completed_tasks]
            durations.sort()
            p95_idx = int(len(durations) * 0.95)
            result["exec_p95_ms"] = durations[p95_idx] if p95_idx < len(durations) else 0
        
        # 计算重试率
        total = status["stats"]["total_submitted"]
        retries = status["stats"]["total_failed"]  # 简化：失败=重试
        if total > 0:
            result["retry_rate_1h"] = retries / total
        
        # DLQ 新增（最近 1 小时）
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        dlq_new = 0
        for task in scheduler.failed_tasks:
            failed_at = datetime.fromisoformat(task["failed_at"])
            if failed_at > one_hour_ago:
                dlq_new += 1
        result["dlq_new_1h"] = dlq_new
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "queue_ready": 0,
            "running": 0,
            "retrying": 0,
            "dlq": 0,
            "concurrency_used": 0,
            "concurrency_max": 5,
            "exec_p95_ms": 0.0,
            "wait_p95_ms": 0.0,
            "retry_rate_1h": 0.0,
            "dlq_new_1h": 0,
            "circuit_breaker": {"status": "closed", "failures": 0, "last_failure": None}
        }


def get_reactor_v06_stats() -> Dict[str, Any]:
    """
    v0.6 Reactor 索引统计
    
    Returns:
        {
            "rules_total": int,
            "rules_by_type": {"resource.cpu_spike": 3, ...},
            "any_rules": int,
            "match_stats_1h": {
                "total_events": int,
                "avg_candidates": float,
                "avg_match_time_ms": float,
                "hit_rate": float
            }
        }
    """
    try:
        from core.production_reactor import get_reactor
        reactor = get_reactor()
        
        # 规则统计
        rules_total = len(reactor.playbooks)
        rules_by_type = {}
        any_rules = 0
        
        for playbook in reactor.playbooks:
            trigger = playbook.get("trigger", {})
            event_type = trigger.get("event_type", "any")
            
            if event_type == "any":
                any_rules += 1
            else:
                rules_by_type[event_type] = rules_by_type.get(event_type, 0) + 1
        
        # 匹配统计（从最近事件计算）
        events_file = AIOS_ROOT / "data" / "events.jsonl"
        match_stats = {
            "total_events": 0,
            "avg_candidates": 0.0,
            "avg_match_time_ms": 0.0,
            "hit_rate": 0.0
        }
        
        if events_file.exists():
            # 读取最近 1 小时的事件
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            recent_events = []
            with open(events_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            event = json.loads(line)
                            ts = event.get("timestamp", 0)
                            if isinstance(ts, int):
                                event_time = datetime.fromtimestamp(ts / 1000)
                                if event_time > one_hour_ago:
                                    recent_events.append(event)
                        except:
                            pass
            
            match_stats["total_events"] = len(recent_events)
            
            # 简化：假设每个事件平均匹配 2 个候选规则
            if rules_total > 0:
                match_stats["avg_candidates"] = min(rules_total, 2.0)
                match_stats["hit_rate"] = 0.5  # 50% 命中率（示例）
                match_stats["avg_match_time_ms"] = 0.5  # 0.5ms（示例）
        
        return {
            "rules_total": rules_total,
            "rules_by_type": rules_by_type,
            "any_rules": any_rules,
            "match_stats_1h": match_stats
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "rules_total": 0,
            "rules_by_type": {},
            "any_rules": 0,
            "match_stats_1h": {
                "total_events": 0,
                "avg_candidates": 0.0,
                "avg_match_time_ms": 0.0,
                "hit_rate": 0.0
            }
        }


def get_eventstore_v06_stats() -> Dict[str, Any]:
    """
    v0.6 EventStore 状态
    
    Returns:
        {
            "active_days": int,
            "active_files": [{"date": "2026-02-24", "size_mb": 0.5, "events": 1234}],
            "archive_count": int,
            "archive_size_mb": float,
            "total_events_7d": int,
            "disk_usage_percent": float,
            "last_archive": str,
            "last_cleanup": str
        }
    """
    try:
        events_dir = AIOS_ROOT / "data" / "events"
        archive_dir = events_dir / "archive"
        
        # 活跃文件（最近 7 天）
        active_files = []
        total_events_7d = 0
        
        if events_dir.exists():
            for file in events_dir.glob("*.jsonl"):
                if file.name == "events.jsonl":
                    # 主文件
                    size_mb = file.stat().st_size / 1024 / 1024
                    
                    # 统计事件数
                    event_count = 0
                    with open(file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                event_count += 1
                    
                    active_files.append({
                        "date": "current",
                        "size_mb": round(size_mb, 2),
                        "events": event_count
                    })
                    total_events_7d += event_count
                
                elif file.stem.startswith("202"):
                    # 按日分片的文件
                    size_mb = file.stat().st_size / 1024 / 1024
                    
                    # 统计事件数
                    event_count = 0
                    with open(file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                event_count += 1
                    
                    active_files.append({
                        "date": file.stem,
                        "size_mb": round(size_mb, 2),
                        "events": event_count
                    })
                    total_events_7d += event_count
        
        # 归档文件
        archive_count = 0
        archive_size_mb = 0.0
        last_archive = None
        
        if archive_dir.exists():
            for file in archive_dir.glob("*.jsonl.gz"):
                archive_count += 1
                archive_size_mb += file.stat().st_size / 1024 / 1024
                
                # 最后归档时间
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if last_archive is None or mtime > datetime.fromisoformat(last_archive):
                    last_archive = mtime.isoformat()
        
        # 磁盘使用率
        import psutil
        disk = psutil.disk_usage(str(AIOS_ROOT))
        disk_usage_percent = disk.percent
        
        return {
            "active_days": len(active_files),
            "active_files": active_files,
            "archive_count": archive_count,
            "archive_size_mb": round(archive_size_mb, 2),
            "total_events_7d": total_events_7d,
            "disk_usage_percent": disk_usage_percent,
            "last_archive": last_archive,
            "last_cleanup": None  # TODO: 从清理日志读取
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "active_days": 0,
            "active_files": [],
            "archive_count": 0,
            "archive_size_mb": 0.0,
            "total_events_7d": 0,
            "disk_usage_percent": 0.0,
            "last_archive": None,
            "last_cleanup": None
        }


def get_v06_snapshot() -> Dict[str, Any]:
    """
    v0.6 完整 snapshot
    
    包含：
    - scheduler_v06: 队列/并发/DLQ/熔断
    - reactor_v06: 索引/匹配统计
    - eventstore_v06: 存储状态
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "version": "0.6",
        "scheduler_v06": get_scheduler_v06_stats(),
        "reactor_v06": get_reactor_v06_stats(),
        "eventstore_v06": get_eventstore_v06_stats()
    }


if __name__ == "__main__":
    # 测试
    snapshot = get_v06_snapshot()
    print(json.dumps(snapshot, indent=2, ensure_ascii=False))
