"""
ChangeDetector - 变化感知模块
监控系统指标的变化趋势，识别"势"的转变
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import deque


class ChangeDetector:
    """变化检测器 - 监控指标变化趋势"""
    
    # 趋势类型（对应易经的"势"）
    TREND_RISING = "rising"      # 上升期（泰卦）
    TREND_FALLING = "falling"    # 下降期（否卦）
    TREND_VOLATILE = "volatile"  # 波动期（屯卦）
    TREND_STABLE = "stable"      # 稳定期（恒卦）
    
    def __init__(self, window_size: int = 10, threshold: float = 0.1):
        """
        Args:
            window_size: 滑动窗口大小（最近N个数据点）
            threshold: 变化阈值（超过此值认为有显著变化）
        """
        self.window_size = window_size
        self.threshold = threshold
        self.history = deque(maxlen=window_size)
    
    def add_data_point(self, value: float, timestamp: datetime = None):
        """添加新数据点"""
        if timestamp is None:
            timestamp = datetime.now()
        self.history.append({"value": value, "timestamp": timestamp})
    
    def detect_trend(self) -> Tuple[str, float]:
        """
        检测当前趋势
        
        Returns:
            (trend_type, confidence) - 趋势类型和置信度（0-1）
        """
        if len(self.history) < 3:
            return self.TREND_STABLE, 0.0
        
        values = [point["value"] for point in self.history]
        
        # 计算线性回归斜率（简化版）
        n = len(values)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # 计算标准差（波动性）
        variance = sum((v - y_mean) ** 2 for v in values) / n
        std_dev = variance ** 0.5
        
        # 归一化斜率（相对于均值）
        if y_mean != 0:
            normalized_slope = slope / y_mean
        else:
            normalized_slope = 0
        
        # 归一化标准差
        if y_mean != 0:
            normalized_std = std_dev / y_mean
        else:
            normalized_std = 0
        
        # 判断趋势
        if normalized_std > self.threshold * 2:
            # 高波动
            return self.TREND_VOLATILE, min(normalized_std, 1.0)
        elif normalized_slope > self.threshold:
            # 上升
            return self.TREND_RISING, min(abs(normalized_slope), 1.0)
        elif normalized_slope < -self.threshold:
            # 下降
            return self.TREND_FALLING, min(abs(normalized_slope), 1.0)
        else:
            # 稳定
            return self.TREND_STABLE, 1.0 - normalized_std
    
    def get_summary(self) -> Dict:
        """获取当前状态摘要"""
        if len(self.history) == 0:
            return {
                "trend": self.TREND_STABLE,
                "confidence": 0.0,
                "current_value": None,
                "mean": None,
                "std_dev": None,
                "data_points": 0
            }
        
        trend, confidence = self.detect_trend()
        values = [point["value"] for point in self.history]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        return {
            "trend": trend,
            "confidence": round(confidence, 3),
            "current_value": round(values[-1], 3),
            "mean": round(mean, 3),
            "std_dev": round(std_dev, 3),
            "data_points": len(values),
            "window_size": self.window_size
        }


class SystemChangeMonitor:
    """系统变化监控器 - 监控多个指标"""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        
        # 为每个关键指标创建检测器
        self.detectors = {
            "success_rate": ChangeDetector(window_size=10, threshold=0.1),
            "avg_duration": ChangeDetector(window_size=10, threshold=0.15),
            "error_rate": ChangeDetector(window_size=10, threshold=0.1),
            "cost": ChangeDetector(window_size=10, threshold=0.2),
        }
    
    def load_recent_tasks(self, hours: int = 24) -> List[Dict]:
        """加载最近的任务数据"""
        tasks_file = self.data_dir / "tasks.jsonl"
        if not tasks_file.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        tasks = []
        
        with open(tasks_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    task = json.loads(line)
                    timestamp = task.get("timestamp", "")
                    if not timestamp:
                        continue
                    task_time = datetime.fromisoformat(timestamp)
                    if task_time >= cutoff_time:
                        tasks.append(task)
                except (ValueError, json.JSONDecodeError):
                    continue
        
        return tasks
    
    def update_from_tasks(self, tasks: List[Dict]):
        """从任务数据更新检测器"""
        if not tasks:
            return
        
        # 按时间排序
        tasks = sorted(tasks, key=lambda t: t.get("timestamp", ""))
        
        # 按小时分组统计
        hourly_stats = {}
        for task in tasks:
            timestamp = datetime.fromisoformat(task.get("timestamp", ""))
            hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
            
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {
                    "total": 0,
                    "success": 0,
                    "duration_sum": 0,
                    "cost_sum": 0,
                }
            
            stats = hourly_stats[hour_key]
            stats["total"] += 1
            if task.get("status") == "completed":
                stats["success"] += 1
            stats["duration_sum"] += task.get("duration", 0)
            stats["cost_sum"] += task.get("cost", 0)
        
        # 更新检测器
        for hour_key in sorted(hourly_stats.keys()):
            stats = hourly_stats[hour_key]
            
            # 成功率
            success_rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            self.detectors["success_rate"].add_data_point(success_rate, hour_key)
            
            # 平均耗时
            avg_duration = stats["duration_sum"] / stats["total"] if stats["total"] > 0 else 0
            self.detectors["avg_duration"].add_data_point(avg_duration, hour_key)
            
            # 错误率
            error_rate = 1 - success_rate
            self.detectors["error_rate"].add_data_point(error_rate, hour_key)
            
            # 平均成本
            avg_cost = stats["cost_sum"] / stats["total"] if stats["total"] > 0 else 0
            self.detectors["cost"].add_data_point(avg_cost, hour_key)
    
    def get_all_trends(self) -> Dict:
        """获取所有指标的趋势"""
        return {
            metric: detector.get_summary()
            for metric, detector in self.detectors.items()
        }
    
    def get_overall_state(self) -> str:
        """
        获取系统整体状态（简化版卦象）
        
        Returns:
            "泰卦" - 顺利期（成功率上升，成本下降）
            "否卦" - 危机期（成功率下降，错误率上升）
            "屯卦" - 困难期（高波动，不稳定）
            "恒卦" - 稳定期（各项指标平稳）
        """
        trends = self.get_all_trends()
        
        success_trend = trends["success_rate"]["trend"]
        error_trend = trends["error_rate"]["trend"]
        
        # 简化判断逻辑
        if success_trend == ChangeDetector.TREND_RISING and error_trend == ChangeDetector.TREND_FALLING:
            return "泰卦"  # 顺利期
        elif success_trend == ChangeDetector.TREND_FALLING or error_trend == ChangeDetector.TREND_RISING:
            return "否卦"  # 危机期
        elif success_trend == ChangeDetector.TREND_VOLATILE or error_trend == ChangeDetector.TREND_VOLATILE:
            return "屯卦"  # 困难期
        else:
            return "恒卦"  # 稳定期


def main():
    """测试变化检测器"""
    print("=== ChangeDetector 测试 ===\n")
    
    # 测试1：模拟上升趋势
    print("测试1：上升趋势（泰卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.5 + i * 0.05)  # 从0.5上升到0.95
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']}")
    print(f"  当前值: {summary['current_value']}")
    print(f"  均值: {summary['mean']}\n")
    
    # 测试2：模拟下降趋势
    print("测试2：下降趋势（否卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.9 - i * 0.05)  # 从0.9下降到0.45
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']}")
    print(f"  当前值: {summary['current_value']}")
    print(f"  均值: {summary['mean']}\n")
    
    # 测试3：模拟波动趋势
    print("测试3：波动趋势（屯卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    import random
    random.seed(42)
    for i in range(10):
        detector.add_data_point(0.7 + random.uniform(-0.2, 0.2))  # 0.5-0.9波动
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']}")
    print(f"  当前值: {summary['current_value']}")
    print(f"  均值: {summary['mean']}\n")
    
    # 测试4：模拟稳定趋势
    print("测试4：稳定趋势（恒卦）")
    detector = ChangeDetector(window_size=10, threshold=0.1)
    for i in range(10):
        detector.add_data_point(0.85 + random.uniform(-0.02, 0.02))  # 0.83-0.87小幅波动
    
    summary = detector.get_summary()
    print(f"  趋势: {summary['trend']}")
    print(f"  置信度: {summary['confidence']}")
    print(f"  当前值: {summary['current_value']}")
    print(f"  均值: {summary['mean']}\n")
    
    # 测试5：系统监控器（如果有真实数据）
    print("测试5：系统监控器")
    monitor = SystemChangeMonitor()
    tasks = monitor.load_recent_tasks(hours=24)
    
    if tasks:
        print(f"  加载了 {len(tasks)} 个任务")
        monitor.update_from_tasks(tasks)
        
        trends = monitor.get_all_trends()
        print("\n  各指标趋势:")
        for metric, summary in trends.items():
            print(f"    {metric}: {summary['trend']} (置信度: {summary['confidence']})")
        
        overall = monitor.get_overall_state()
        print(f"\n  系统整体状态: {overall}")
    else:
        print("  没有找到任务数据，跳过测试")


if __name__ == "__main__":
    main()
