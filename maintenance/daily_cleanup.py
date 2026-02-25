#!/usr/bin/env python3
"""
每日自动清理脚本
清理 __pycache__、.pyc、.bak、临时文件等
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

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
                print(f"  ⚠️  无法删除 {pycache_dir}: {e}")
    
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
                    print(f"  ⚠️  无法删除 {fp}: {e}")
    
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
                    print(f"  ⚠️  无法删除 {fp}: {e}")
    
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
                    print(f"  ⚠️  无法删除 {fp}: {e}")
    
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
                    print(f"  ⚠️  无法删除 {fp}: {e}")
    
    return count, size

def main():
    """主清理流程"""
    print(f"=== 每日自动清理 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print()
    
    # 清理目标目录
    targets = [
        Path(r"C:\Users\A\.openclaw\workspace"),
        Path(r"C:\Users\A\Desktop"),
    ]
    
    total_count = 0
    total_size = 0
    
    for target in targets:
        if not target.exists():
            continue
        
        print(f"清理目录: {target}")
        
        # 1. __pycache__
        count, size = cleanup_pycache(target)
        if count > 0:
            print(f"  ✅ __pycache__: 删除 {count} 个目录，释放 {size / 1024:.2f} KB")
            total_count += count
            total_size += size
        
        # 2. .pyc 文件
        count, size = cleanup_pyc_files(target)
        if count > 0:
            print(f"  ✅ .pyc 文件: 删除 {count} 个，释放 {size / 1024:.2f} KB")
            total_count += count
            total_size += size
        
        # 3. .bak 文件
        count, size = cleanup_backup_files(target)
        if count > 0:
            print(f"  ✅ .bak 文件: 删除 {count} 个，释放 {size / 1024:.2f} KB")
            total_count += count
            total_size += size
        
        # 4. 临时文件
        count, size = cleanup_temp_files(target)
        if count > 0:
            print(f"  ✅ 临时文件: 删除 {count} 个，释放 {size / 1024:.2f} KB")
            total_count += count
            total_size += size
        
        # 5. 旧日志（>7天）
        count, size = cleanup_old_logs(target, days=7)
        if count > 0:
            print(f"  ✅ 旧日志: 删除 {count} 个，释放 {size / 1024:.2f} KB")
            total_count += count
            total_size += size
        
        print()
    
    print("=== 清理完成 ===")
    if total_count > 0:
        print(f"总计: 删除 {total_count} 个文件/目录，释放 {total_size / 1024 / 1024:.2f} MB")
    else:
        print("无需清理")

if __name__ == "__main__":
    main()
