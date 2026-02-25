"""
CPU 压力生成器 - 多进程版本
真正打满 CPU 到指定百分比
"""
import multiprocessing
import time
import sys


def cpu_burn(duration_seconds):
    """单核 CPU 燃烧"""
    end_time = time.time() + duration_seconds
    while time.time() < end_time:
        # 密集计算
        result = 1.0
        for _ in range(100000):
            result *= 1.0001


def generate_cpu_load(target_percent, duration_seconds):
    """
    生成指定百分比的 CPU 负载
    
    Args:
        target_percent: 目标 CPU 使用率（0-100）
        duration_seconds: 持续时间（秒）
    """
    cpu_count = multiprocessing.cpu_count()
    target_cores = int(cpu_count * target_percent / 100)
    
    print(f"CPU 核心数: {cpu_count}")
    print(f"目标负载: {target_percent}% ({target_cores} 核)")
    print(f"持续时间: {duration_seconds} 秒")
    
    # 启动多个进程
    processes = []
    for i in range(target_cores):
        p = multiprocessing.Process(target=cpu_burn, args=(duration_seconds,))
        p.start()
        processes.append(p)
        print(f"启动进程 {i+1}/{target_cores}")
    
    # 等待所有进程完成
    for p in processes:
        p.join()
    
    print("完成")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python cpu_stress.py <target_percent> <duration_seconds>")
        print("示例: python cpu_stress.py 85 20")
        sys.exit(1)
    
    target = int(sys.argv[1])
    duration = int(sys.argv[2])
    
    generate_cpu_load(target, duration)
