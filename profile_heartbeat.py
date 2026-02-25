"""
分析心跳性能瓶颈
"""
import time
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))


def profile_heartbeat():
    """分析心跳各部分耗时"""
    from heartbeat_runner_optimized import (
        warmup_components,
        check_resources_fast,
        log_resource_snapshot,
        get_monitor
    )
    
    print("=" * 60)
    print("心跳性能分析")
    print("=" * 60)
    
    # 预热
    print("\n1. 预热组件...")
    warmup_components()
    
    print("\n2. 分析各部分耗时...")
    
    # 测试 check_resources_fast
    times = []
    for _ in range(10):
        start = time.time()
        cpu, mem = check_resources_fast()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"   check_resources_fast: {sum(times)/len(times):.1f}ms (平均)")
    
    # 测试 log_resource_snapshot
    times = []
    for _ in range(10):
        start = time.time()
        log_resource_snapshot(50.0, 50.0)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"   log_resource_snapshot: {sum(times)/len(times):.1f}ms (平均)")
    
    # 测试 monitor.record_resources
    monitor = get_monitor()
    times = []
    for _ in range(10):
        start = time.time()
        monitor.record_resources(50.0, 50.0)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"   monitor.record_resources: {sum(times)/len(times):.1f}ms (平均)")
    
    # 测试 monitor.record_heartbeat
    times = []
    for _ in range(10):
        start = time.time()
        monitor.record_heartbeat(100.0, "TEST")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"   monitor.record_heartbeat: {sum(times)/len(times):.1f}ms (平均)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    profile_heartbeat()
