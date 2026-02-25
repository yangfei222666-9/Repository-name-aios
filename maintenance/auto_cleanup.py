#!/usr/bin/env python3
"""
AIOS 自动清理维护脚本
每天心跳时运行，保持系统健康
"""

import os
import sys
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 添加 aios 到 Python 路径
WORKSPACE = Path(__file__).parent.parent.parent
AIOS_DIR = WORKSPACE / "aios"
sys.path.insert(0, str(AIOS_DIR))

from core.event_store import get_event_store

MEMORY_DIR = WORKSPACE / "memory"
ARCHIVE_DIR = MEMORY_DIR / "archive"

# 清理规则
KEEP_MEMORY_DAYS = 30  # memory/*.md 保留天数（超过则压缩归档）
DISK_WARNING_THRESHOLD = 80  # 磁盘使用率警告阈值（%）
DISK_CRITICAL_THRESHOLD = 90  # 磁盘使用率危险阈值（%）


def get_disk_usage():
    """获取磁盘使用率"""
    try:
        import psutil
        usage = psutil.disk_usage(str(WORKSPACE))
        return usage.percent
    except ImportError:
        # 如果没有 psutil，用 Windows 命令
        import subprocess
        result = subprocess.run(
            ["powershell", "-Command", 
             f"(Get-PSDrive -Name {WORKSPACE.drive[0]}).Used / (Get-PSDrive -Name {WORKSPACE.drive[0]}).Used + (Get-PSDrive -Name {WORKSPACE.drive[0]}).Free * 100"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
        return 0


def cleanup_events():
    """清理旧的事件文件（使用 EventStore）"""
    try:
        store = get_event_store()
        stats = store.cleanup()
        
        return {
            "status": "cleaned",
            "archived": stats['archived'],
            "deleted": stats['deleted'],
            "saved_mb": round(stats['saved_bytes'] / 1024 / 1024, 2)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def archive_old_memory():
    """归档旧的 memory/*.md 文件"""
    if not MEMORY_DIR.exists():
        return {"status": "skip", "reason": "memory dir not found"}
    
    ARCHIVE_DIR.mkdir(exist_ok=True)
    cutoff_date = datetime.now() - timedelta(days=KEEP_MEMORY_DAYS)
    
    archived = []
    for md_file in MEMORY_DIR.glob("????-??-??.md"):
        try:
            # 从文件名提取日期
            date_str = md_file.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff_date:
                # 压缩并归档
                gz_file = ARCHIVE_DIR / f"{md_file.name}.gz"
                with open(md_file, 'rb') as f_in:
                    with gzip.open(gz_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # 删除原文件
                md_file.unlink()
                archived.append(md_file.name)
        except ValueError:
            continue
    
    return {
        "status": "archived",
        "count": len(archived),
        "files": archived[:5]  # 只显示前5个
    }


def cleanup_temp_files():
    """清理临时文件"""
    cleaned = []
    
    # 清理 .bak 文件（超过7天的）
    cutoff_time = datetime.now() - timedelta(days=7)
    for bak_file in WORKSPACE.rglob("*.bak"):
        if bak_file.stat().st_mtime < cutoff_time.timestamp():
            bak_file.unlink()
            cleaned.append(str(bak_file.relative_to(WORKSPACE)))
    
    # 清理 __pycache__
    for pycache in WORKSPACE.rglob("__pycache__"):
        shutil.rmtree(pycache, ignore_errors=True)
        cleaned.append(str(pycache.relative_to(WORKSPACE)))
    
    return {
        "status": "cleaned",
        "count": len(cleaned),
        "files": cleaned[:5]
    }


def check_disk_space():
    """检查磁盘空间"""
    usage = get_disk_usage()
    
    status = "ok"
    if usage >= DISK_CRITICAL_THRESHOLD:
        status = "critical"
    elif usage >= DISK_WARNING_THRESHOLD:
        status = "warning"
    
    return {
        "status": status,
        "usage_percent": round(usage, 1),
        "threshold_warning": DISK_WARNING_THRESHOLD,
        "threshold_critical": DISK_CRITICAL_THRESHOLD
    }


def main():
    """主函数"""
    print("🧹 AIOS 自动清理维护")
    print("=" * 50)
    
    results = {}
    
    # 1. 清理事件文件
    print("\n📦 清理事件日志...")
    results['events'] = cleanup_events()
    if results['events']['status'] == 'cleaned':
        print(f"   ✅ 归档 {results['events']['archived']} 个文件")
        print(f"   ✅ 删除 {results['events']['deleted']} 个文件")
        print(f"   💾 节省 {results['events']['saved_mb']} MB")
    elif results['events']['status'] == 'error':
        print(f"   ❌ 错误: {results['events']['error']}")
    
    # 2. 归档旧记忆
    print("\n📚 归档旧记忆文件...")
    results['memory'] = archive_old_memory()
    if results['memory']['status'] == 'archived':
        print(f"   ✅ 归档 {results['memory']['count']} 个文件")
        if results['memory']['files']:
            print(f"   📁 {', '.join(results['memory']['files'])}")
    
    # 3. 清理临时文件
    print("\n🗑️  清理临时文件...")
    results['temp'] = cleanup_temp_files()
    if results['temp']['count'] > 0:
        print(f"   ✅ 清理 {results['temp']['count']} 个文件/目录")
    else:
        print("   ✅ 无需清理")
    
    # 4. 检查磁盘空间
    print("\n💾 检查磁盘空间...")
    results['disk'] = check_disk_space()
    usage = results['disk']['usage_percent']
    
    if results['disk']['status'] == 'critical':
        print(f"   🔴 危险！磁盘使用率 {usage}% (>={DISK_CRITICAL_THRESHOLD}%)")
        print("   ⚠️  建议立即清理大文件")
    elif results['disk']['status'] == 'warning':
        print(f"   🟡 警告：磁盘使用率 {usage}% (>={DISK_WARNING_THRESHOLD}%)")
    else:
        print(f"   ✅ 磁盘使用率 {usage}%")
    
    # 5. 保存清理报告
    report_file = AIOS_DIR / "data" / "cleanup_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 清理报告已保存: {report_file.relative_to(WORKSPACE)}")
    
    # 6. 输出心跳格式
    print("\n" + "=" * 50)
    if results['disk']['status'] == 'critical':
        print("CLEANUP_CRITICAL")
    elif results['disk']['status'] == 'warning':
        print("CLEANUP_WARNING")
    else:
        print("CLEANUP_OK")


if __name__ == "__main__":
    main()
