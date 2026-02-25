"""
AIOS 性能监控工具
实时监控心跳性能和系统健康度
"""
import time
import json
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Dict, List


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size=100):
        """
        初始化监控器
        
        Args:
            window_size: 滑动窗口大小（保留最近 N 次记录）
        """
        self.window_size = window_size
        self.heartbeat_times = deque(maxlen=window_size)
        self.resource_snapshots = deque(maxlen=window_size)
        self.alerts = deque(maxlen=50)
        
        self.stats_file = Path(__file__).parent / "data" / "performance_stats.jsonl"
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    def record_heartbeat(self, duration_ms: float, result: str):
        """记录心跳性能"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "result": result
        }
        
        self.heartbeat_times.append(record)
        
        # 持久化
        with open(self.stats_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
    
    def record_resources(self, cpu_percent: float, memory_percent: float):
        """记录资源使用"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent
        }
        
        self.resource_snapshots.append(record)
    
    def record_alert(self, alert_type: str, message: str):
        """记录告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message
        }
        
        self.alerts.append(alert)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        if not self.heartbeat_times:
            return {
                "heartbeat": {"count": 0},
                "resources": {"count": 0},
                "alerts": {"count": 0}
            }
        
        # 心跳统计
        durations = [r["duration_ms"] for r in self.heartbeat_times]
        heartbeat_stats = {
            "count": len(durations),
            "avg_ms": sum(durations) / len(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "p50_ms": sorted(durations)[len(durations) // 2],
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)],
            "p99_ms": sorted(durations)[int(len(durations) * 0.99)]
        }
        
        # 资源统计
        if self.resource_snapshots:
            cpu_values = [r["cpu_percent"] for r in self.resource_snapshots]
            memory_values = [r["memory_percent"] for r in self.resource_snapshots]
            
            resource_stats = {
                "count": len(self.resource_snapshots),
                "cpu": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "min": min(cpu_values),
                    "max": max(cpu_values)
                },
                "memory": {
                    "avg": sum(memory_values) / len(memory_values),
                    "min": min(memory_values),
                    "max": max(memory_values)
                }
            }
        else:
            resource_stats = {"count": 0}
        
        # 告警统计
        alert_stats = {
            "count": len(self.alerts),
            "recent": list(self.alerts)[-5:]  # 最近 5 条
        }
        
        return {
            "heartbeat": heartbeat_stats,
            "resources": resource_stats,
            "alerts": alert_stats
        }
    
    def print_stats(self):
        """打印统计信息"""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("AIOS 性能监控报告")
        print("=" * 60)
        
        # 心跳性能
        hb = stats["heartbeat"]
        if hb["count"] > 0:
            print(f"\n📊 心跳性能（最近 {hb['count']} 次）:")
            print(f"   平均: {hb['avg_ms']:.1f}ms")
            print(f"   最快: {hb['min_ms']:.1f}ms")
            print(f"   最慢: {hb['max_ms']:.1f}ms")
            print(f"   P50:  {hb['p50_ms']:.1f}ms")
            print(f"   P95:  {hb['p95_ms']:.1f}ms")
            print(f"   P99:  {hb['p99_ms']:.1f}ms")
        
        # 资源使用
        res = stats["resources"]
        if res["count"] > 0:
            print(f"\n💻 资源使用（最近 {res['count']} 次）:")
            print(f"   CPU:    平均 {res['cpu']['avg']:.1f}%  (最低 {res['cpu']['min']:.1f}%, 最高 {res['cpu']['max']:.1f}%)")
            print(f"   内存:   平均 {res['memory']['avg']:.1f}%  (最低 {res['memory']['min']:.1f}%, 最高 {res['memory']['max']:.1f}%)")
        
        # 告警
        alerts = stats["alerts"]
        if alerts["count"] > 0:
            print(f"\n⚠️ 告警（总计 {alerts['count']} 条）:")
            for alert in alerts["recent"]:
                print(f"   [{alert['timestamp']}] {alert['type']}: {alert['message']}")
        
        print("\n" + "=" * 60)
    
    def check_health(self) -> Dict:
        """健康检查"""
        stats = self.get_stats()
        
        health = {
            "status": "healthy",
            "issues": []
        }
        
        # 检查心跳性能
        hb = stats["heartbeat"]
        if hb["count"] > 0:
            if hb["avg_ms"] > 100:
                health["status"] = "degraded"
                health["issues"].append(f"心跳平均延迟过高: {hb['avg_ms']:.1f}ms")
            
            if hb["p95_ms"] > 200:
                health["status"] = "degraded"
                health["issues"].append(f"心跳 P95 延迟过高: {hb['p95_ms']:.1f}ms")
        
        # 检查资源使用
        res = stats["resources"]
        if res["count"] > 0:
            if res["cpu"]["avg"] > 80:
                health["status"] = "warning"
                health["issues"].append(f"CPU 使用率过高: {res['cpu']['avg']:.1f}%")
            
            if res["memory"]["avg"] > 85:
                health["status"] = "warning"
                health["issues"].append(f"内存使用率过高: {res['memory']['avg']:.1f}%")
        
        # 检查告警
        if stats["alerts"]["count"] > 10:
            health["status"] = "warning"
            health["issues"].append(f"告警数量过多: {stats['alerts']['count']} 条")
        
        return health


# 全局监控器实例
_monitor = None


def get_monitor() -> PerformanceMonitor:
    """获取全局监控器"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def monitor_heartbeat(func):
    """心跳监控装饰器"""
    def wrapper(*args, **kwargs):
        monitor = get_monitor()
        
        start = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start) * 1000
        
        monitor.record_heartbeat(duration_ms, str(result))
        
        return result
    
    return wrapper


if __name__ == "__main__":
    # 测试监控器
    monitor = PerformanceMonitor()
    
    # 模拟记录
    import random
    
    for i in range(20):
        monitor.record_heartbeat(
            duration_ms=random.uniform(2, 10),
            result="HEARTBEAT_OK"
        )
        
        monitor.record_resources(
            cpu_percent=random.uniform(20, 60),
            memory_percent=random.uniform(40, 70)
        )
        
        time.sleep(0.1)
    
    # 打印统计
    monitor.print_stats()
    
    # 健康检查
    health = monitor.check_health()
    print(f"\n健康状态: {health['status']}")
    if health['issues']:
        print("问题:")
        for issue in health['issues']:
            print(f"  - {issue}")
