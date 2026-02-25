"""
AIOS 实时性能监控
持续监控心跳性能和系统健康度
"""
import time
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_runner_optimized import run_heartbeat_minimal
from performance_monitor import get_monitor


def run_continuous_monitoring(interval_seconds=5, duration_minutes=5):
    """
    持续监控
    
    Args:
        interval_seconds: 心跳间隔（秒）
        duration_minutes: 监控时长（分钟）
    """
    monitor = get_monitor()
    
    total_runs = int((duration_minutes * 60) / interval_seconds)
    
    print("=" * 60)
    print(f"AIOS 实时性能监控")
    print(f"监控时长: {duration_minutes} 分钟")
    print(f"心跳间隔: {interval_seconds} 秒")
    print(f"预计运行: {total_runs} 次")
    print("=" * 60)
    print()
    
    try:
        for i in range(total_runs):
            # 运行心跳
            result = run_heartbeat_minimal()
            
            # 打印结果
            print(f"[{i+1}/{total_runs}] {result}")
            
            # 每 10 次打印一次统计
            if (i + 1) % 10 == 0:
                print()
                monitor.print_stats()
                
                # 健康检查
                health = monitor.check_health()
                if health["status"] != "healthy":
                    print(f"\n⚠️ 健康状态: {health['status']}")
                    for issue in health["issues"]:
                        print(f"   - {issue}")
                print()
            
            # 等待下次心跳
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        print("\n\n监控已停止（用户中断）")
    
    # 最终统计
    print("\n" + "=" * 60)
    print("最终统计")
    print("=" * 60)
    monitor.print_stats()
    
    # 健康检查
    health = monitor.check_health()
    print(f"\n健康状态: {health['status']}")
    if health['issues']:
        print("问题:")
        for issue in health['issues']:
            print(f"  - {issue}")
    else:
        print("✅ 系统健康")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="AIOS 实时性能监控")
    parser.add_argument("--interval", type=int, default=5, help="心跳间隔（秒），默认 5")
    parser.add_argument("--duration", type=int, default=5, help="监控时长（分钟），默认 5")
    
    args = parser.parse_args()
    
    run_continuous_monitoring(
        interval_seconds=args.interval,
        duration_minutes=args.duration
    )
