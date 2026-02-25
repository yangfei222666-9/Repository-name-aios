#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIOS 真实场景演示 - 文件监控 + 自动备份
展示完整闭环：监控 → 检测变化 → 自动备份 → 验证 → 通知
"""
import sys
import time
import json
import shutil
from pathlib import Path
from datetime import datetime
import hashlib

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from observability import span, METRICS, get_logger

logger = get_logger("FileMonitorDemo")

def calculate_hash(file_path: Path) -> str:
    """计算文件哈希"""
    if not file_path.exists():
        return ""
    
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def backup_file(source: Path, backup_dir: Path) -> Path:
    """备份文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.stem}_{timestamp}{source.suffix}"
    backup_path = backup_dir / backup_name
    
    shutil.copy2(source, backup_path)
    return backup_path

def print_banner(text: str):
    """打印横幅"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def main():
    """主函数"""
    print_banner("🚀 AIOS 真实场景演示 - 文件监控 + 自动备份")
    
    # 创建演示环境
    demo_dir = Path(__file__).parent / "demo_workspace"
    demo_dir.mkdir(exist_ok=True)
    
    backup_dir = demo_dir / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    watched_file = demo_dir / "important_config.json"
    
    # 初始化文件
    initial_data = {
        "version": "1.0",
        "settings": {
            "debug": False,
            "timeout": 30
        }
    }
    
    print("\n📁 创建演示环境...")
    print(f"   监控文件: {watched_file}")
    print(f"   备份目录: {backup_dir}")
    
    with open(watched_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f, indent=2, ensure_ascii=False)
    
    print("   ✅ 环境创建完成")
    
    # 开始监控
    print("\n🔍 开始监控文件变化（每 2 秒检查一次）...")
    print("   提示：请在另一个窗口修改文件，或等待自动修改演示\n")
    
    last_hash = calculate_hash(watched_file)
    check_count = 0
    backup_count = 0
    
    # 自动修改计划
    auto_modify_at = 3  # 第3次检查时自动修改
    
    try:
        for i in range(10):  # 检查 10 次
            check_count += 1
            
            with span(f"file-check-{check_count}"):
                # 自动修改演示（第3次检查）
                if check_count == auto_modify_at:
                    print(f"{'='*70}")
                    print("  🔧 自动修改文件（模拟用户编辑）...")
                    print(f"{'='*70}\n")
                    
                    modified_data = initial_data.copy()
                    modified_data["version"] = "1.1"
                    modified_data["settings"]["debug"] = True
                    modified_data["settings"]["timeout"] = 60
                    
                    with open(watched_file, "w", encoding="utf-8") as f:
                        json.dump(modified_data, f, indent=2, ensure_ascii=False)
                    
                    print("   ✅ 文件已修改")
                    time.sleep(0.5)
                
                # 检查文件变化
                current_hash = calculate_hash(watched_file)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if current_hash != last_hash:
                    print(f"[{timestamp}] 🚨 检测到文件变化！")
                    METRICS.inc_counter("file.changes.detected", 1, labels={"file": watched_file.name})
                    
                    # 触发自动备份
                    print(f"\n{'='*70}")
                    print("  💾 触发 AIOS 自动备份...")
                    print(f"{'='*70}\n")
                    
                    with span("auto-backup"):
                        try:
                            backup_path = backup_file(watched_file, backup_dir)
                            backup_count += 1
                            
                            print(f"   ✅ 备份成功: {backup_path.name}")
                            METRICS.inc_counter("file.backups.success", 1, labels={"file": watched_file.name})
                            
                            # 验证备份
                            backup_hash = calculate_hash(backup_path)
                            if backup_hash == current_hash:
                                print(f"   ✅ 备份验证通过（哈希匹配）")
                                METRICS.inc_counter("file.backups.verified", 1)
                            else:
                                print(f"   ❌ 备份验证失败（哈希不匹配）")
                                METRICS.inc_counter("file.backups.verification_failed", 1)
                        
                        except Exception as e:
                            print(f"   ❌ 备份失败: {e}")
                            METRICS.inc_counter("file.backups.failure", 1)
                    
                    print(f"\n{'='*70}")
                    print("  🔄 继续监控...")
                    print(f"{'='*70}\n")
                    
                    last_hash = current_hash
                else:
                    print(f"[{timestamp}] ✅ 检查 #{check_count}: 文件未变化")
                    METRICS.inc_counter("file.checks.no_change", 1)
                
                # 记录检查耗时
                METRICS.observe("file.check_duration", 0.01, labels={"file": watched_file.name})
                
                # 写入共享 Metrics 文件（供 Dashboard 读取）
                shared_metrics_file = demo_dir.parent / "data" / "metrics_shared.json"
                shared_metrics_file.parent.mkdir(exist_ok=True)
                METRICS.write_snapshot(str(shared_metrics_file))
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  监控已停止")
    
    # 显示统计
    print_banner("📊 监控统计")
    
    snapshot = METRICS.snapshot()
    
    changes_detected = 0
    backups_success = 0
    backups_verified = 0
    
    for counter in snapshot.get("counters", []):
        if counter["name"] == "file.changes.detected":
            changes_detected = counter["value"]
        elif counter["name"] == "file.backups.success":
            backups_success = counter["value"]
        elif counter["name"] == "file.backups.verified":
            backups_verified = counter["value"]
    
    print(f"\n✅ 总检查次数: {check_count}")
    print(f"🚨 检测到变化: {int(changes_detected)} 次")
    print(f"💾 自动备份: {int(backups_success)} 次")
    print(f"✅ 备份验证: {int(backups_verified)} 次")
    
    # 显示备份文件列表
    backup_files = sorted(backup_dir.glob("*.json"))
    if backup_files:
        print(f"\n📁 备份文件列表:")
        for bf in backup_files:
            size = bf.stat().st_size
            mtime = datetime.fromtimestamp(bf.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   • {bf.name} ({size} bytes, {mtime})")
    
    print_banner("✅ 演示完成！")
    
    print("\n💡 这个演示展示了 AIOS 的核心能力：")
    print("   1. 🔍 持续监控 - 每 2 秒检查文件变化（哈希对比）")
    print("   2. 🚨 变化检测 - 自动检测文件修改")
    print("   3. 💾 自动备份 - 检测到变化立即备份（带时间戳）")
    print("   4. ✅ 验证机制 - 备份后验证哈希确保完整性")
    print("   5. 📊 数据记录 - 所有事件记录到 Metrics 和 Logger")
    
    print("\n📁 查看详细数据：")
    print("   • 监控文件: " + str(watched_file))
    print("   • 备份目录: " + str(backup_dir))
    print("   • 日志: aios/logs/aios.jsonl")
    print("   • Dashboard: python aios.py dashboard")
    
    # 自动清理演示环境
    print("\n🧹 清理演示环境...")
    import shutil
    try:
        shutil.rmtree(demo_dir)
        print("   ✅ 清理完成")
    except Exception as e:
        print(f"   ⚠️  清理失败: {e}")

if __name__ == "__main__":
    main()
