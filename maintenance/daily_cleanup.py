#!/usr/bin/env python3
"""
每日自动清理脚本
清理 __pycache__、.pyc、.bak、临时文件等
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

def _safe_print(s: str) -> None:
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("ascii", "ignore").decode("ascii"))


def cleanup_pycache(root_dir):
    """清理 __pycache__ 目录"""
    count = 0
    size = 0
    
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            try:
                dir_size = sum(os.path.getsize(os.path.join(pycache_dir, f)) 
                              for f in os.listdir(pycache_dir) 
                              if os.path.isfile(os.path.join(pycache_dir, f)))
                shutil.rmtree(pycache_dir)
                count += 1
                size += dir_size
            except Exception as e:
                _safe_print(f"  WARN cannot delete {pycache_dir}: {e}")
    
    return count, size

def cleanup_pyc_files(root_dir):
    """清理 .pyc 文件"""
    count = 0
    size = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.pyc'):
                fp = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(fp)
                    os.remove(fp)
                    count += 1
                    size += file_size
                except Exception as e:
                    _safe_print(f"  WARN cannot delete {fp}: {e}")
    
    return count, size

def cleanup_backup_files(root_dir):
    """清理 .bak 文件"""
    count = 0
    size = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.bak'):
                fp = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(fp)
                    os.remove(fp)
                    count += 1
                    size += file_size
                except Exception as e:
                    _safe_print(f"  WARN cannot delete {fp}: {e}")
    
    return count, size

def cleanup_temp_files(root_dir):
    """清理临时文件"""
    count = 0
    size = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.startswith('~') or file.endswith('.tmp') or file.endswith('~'):
                fp = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(fp)
                    os.remove(fp)
                    count += 1
                    size += file_size
                except Exception as e:
                    _safe_print(f"  WARN cannot delete {fp}: {e}")
    
    return count, size

def cleanup_old_logs(root_dir, days=7):
    """清理旧日志文件（>7天）"""
    count = 0
    size = 0
    cutoff = datetime.now().timestamp() - (days * 86400)
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.log'):
                fp = os.path.join(root, file)
                try:
                    if os.path.getmtime(fp) < cutoff:
                        file_size = os.path.getsize(fp)
                        os.remove(fp)
                        count += 1
                        size += file_size
                except Exception as e:
                    _safe_print(f"  WARN cannot delete {fp}: {e}")
    
    return count, size

def main():
    """主清理流程"""
    if sys.platform == "win32":
        try:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        except Exception:
            pass

    try:
        from aios.agent_system.config_center import openclaw_workspace_root
        targets = [openclaw_workspace_root()]
    except Exception:
        targets = [Path.home() / ".openclaw" / "workspace"]

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _safe_print(f"daily_cleanup start {ts}")

    total_items = 0
    total_bytes = 0
    scanned_targets = []

    for target in targets:
        if not target.exists():
            continue
        scanned_targets.append(str(target))
        _safe_print(f"cleaning {target}")

        count, size = cleanup_pycache(target)
        total_items += count
        total_bytes += size

        count, size = cleanup_pyc_files(target)
        total_items += count
        total_bytes += size

        count, size = cleanup_backup_files(target)
        total_items += count
        total_bytes += size

        count, size = cleanup_temp_files(target)
        total_items += count
        total_bytes += size

        count, size = cleanup_old_logs(target, days=7)
        total_items += count
        total_bytes += size

    summary = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "ok": True,
        "targets": scanned_targets,
        "deleted_items": total_items,
        "freed_bytes": total_bytes,
    }
    print(json.dumps(summary, ensure_ascii=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
