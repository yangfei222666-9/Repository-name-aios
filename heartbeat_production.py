"""
AIOS 生产环境监控（简化版）
每次心跳时调用，记录性能数据
"""
import sys
from pathlib import Path

AIOS_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(AIOS_ROOT))

from heartbeat_runner_optimized import run_heartbeat_minimal
from performance_monitor import get_monitor


def run_production_heartbeat():
    """生产环境心跳（带监控）"""
    try:
        # 运行优化的心跳
        result = run_heartbeat_minimal()
        
        # 获取监控器
        monitor = get_monitor()
        
        # 每 100 次心跳打印一次统计
        if len(monitor.heartbeat_times) % 100 == 0 and len(monitor.heartbeat_times) > 0:
            stats = monitor.get_stats()
            hb = stats["heartbeat"]
            
            print(f"\n[AIOS 性能统计] 最近 {hb['count']} 次心跳:")
            print(f"  平均: {hb['avg_ms']:.1f}ms | P95: {hb['p95_ms']:.1f}ms | P99: {hb['p99_ms']:.1f}ms")
            
            # 健康检查
            health = monitor.check_health()
            if health["status"] != "healthy":
                print(f"  ⚠️ 状态: {health['status']}")
                for issue in health["issues"]:
                    print(f"     - {issue}")
        
        return result
    
    except Exception as e:
        print(f"❌ 心跳失败: {e}")
        return f"HEARTBEAT_ERROR: {e}"


if __name__ == "__main__":
    result = run_production_heartbeat()
    print(result)
