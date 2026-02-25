"""
心跳性能对比测试
"""
import time
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))


def benchmark_heartbeat(runner_module, runs=5):
    """基准测试心跳性能"""
    times = []
    
    for i in range(runs):
        start = time.time()
        
        try:
            if runner_module == "original":
                from heartbeat_runner import run_heartbeat
                result = run_heartbeat()
            elif runner_module == "optimized":
                from heartbeat_runner_optimized import run_heartbeat_optimized
                result = run_heartbeat_optimized()
            elif runner_module == "minimal":
                from heartbeat_runner_optimized import run_heartbeat_minimal
                result = run_heartbeat_minimal()
            
            elapsed = (time.time() - start) * 1000  # 转换为毫秒
            times.append(elapsed)
            
            print(f"  Run {i+1}: {elapsed:.1f}ms - {result}")
        
        except Exception as e:
            print(f"  Run {i+1}: ERROR - {e}")
            times.append(0)
        
        # 短暂休息
        time.sleep(0.5)
    
    # 计算统计
    valid_times = [t for t in times if t > 0]
    if valid_times:
        avg = sum(valid_times) / len(valid_times)
        min_time = min(valid_times)
        max_time = max(valid_times)
        
        return {
            "avg": avg,
            "min": min_time,
            "max": max_time,
            "times": valid_times
        }
    else:
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("AIOS 心跳性能对比测试")
    print("=" * 60)
    
    # 测试原始版本
    print("\n1. 原始版本 (heartbeat_runner.py):")
    original_stats = benchmark_heartbeat("original", runs=3)
    
    if original_stats:
        print(f"\n   平均: {original_stats['avg']:.1f}ms")
        print(f"   最快: {original_stats['min']:.1f}ms")
        print(f"   最慢: {original_stats['max']:.1f}ms")
    
    # 测试优化版本
    print("\n2. 优化版本 (run_heartbeat_optimized):")
    optimized_stats = benchmark_heartbeat("optimized", runs=3)
    
    if optimized_stats:
        print(f"\n   平均: {optimized_stats['avg']:.1f}ms")
        print(f"   最快: {optimized_stats['min']:.1f}ms")
        print(f"   最慢: {optimized_stats['max']:.1f}ms")
    
    # 测试最小化版本
    print("\n3. 最小化版本 (run_heartbeat_minimal):")
    minimal_stats = benchmark_heartbeat("minimal", runs=3)
    
    if minimal_stats:
        print(f"\n   平均: {minimal_stats['avg']:.1f}ms")
        print(f"   最快: {minimal_stats['min']:.1f}ms")
        print(f"   最慢: {minimal_stats['max']:.1f}ms")
    
    # 性能对比
    print("\n" + "=" * 60)
    print("性能对比:")
    print("=" * 60)
    
    if original_stats and optimized_stats:
        speedup = original_stats['avg'] / optimized_stats['avg']
        print(f"优化版本 vs 原始版本: {speedup:.2f}x 加速")
    
    if original_stats and minimal_stats:
        speedup = original_stats['avg'] / minimal_stats['avg']
        print(f"最小化版本 vs 原始版本: {speedup:.2f}x 加速")
    
    if optimized_stats and minimal_stats:
        speedup = optimized_stats['avg'] / minimal_stats['avg']
        print(f"最小化版本 vs 优化版本: {speedup:.2f}x 加速")
    
    print("\n" + "=" * 60)
