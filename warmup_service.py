"""
AIOS 预热服务（持久化）
保持组件在内存中，避免重复初始化
"""
import sys
import time
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_runner_optimized import warmup_components, run_heartbeat_minimal


def run_warmup_service(interval_seconds=5, duration_minutes=60):
    """
    运行预热服务
    
    Args:
        interval_seconds: 心跳间隔
        duration_minutes: 运行时长
    """
    print("=" * 60)
    print("AIOS 预热服务启动")
    print(f"运行时长: {duration_minutes} 分钟")
    print(f"心跳间隔: {interval_seconds} 秒")
    print("=" * 60)
    
    # 预热组件
    warmup_components()
    
    print("\n开始心跳循环...")
    print("-" * 60)
    
    total_runs = int((duration_minutes * 60) / interval_seconds)
    
    try:
        for i in range(total_runs):
            start = time.time()
            
            # 运行心跳
            result = run_heartbeat_minimal()
            
            elapsed = (time.time() - start) * 1000
            
            # 打印结果
            print(f"[{i+1:3d}/{total_runs}] {result} (实际耗时: {elapsed:.1f}ms)")
            
            # 等待下次心跳
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n服务已停止（用户中断）")
    
    print("\n" + "=" * 60)
    print("预热服务结束")
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS 预热服务")
    parser.add_argument("--interval", type=int, default=5, help="心跳间隔（秒）")
    parser.add_argument("--duration", type=int, default=60, help="运行时长（分钟）")
    
    args = parser.parse_args()
    
    run_warmup_service(
        interval_seconds=args.interval,
        duration_minutes=args.duration
    )
