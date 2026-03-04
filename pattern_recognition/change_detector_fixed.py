"""
ChangeDetector - 变化感知模块（修复版）
监控系统指标的变化趋势，识别"势"的转变
修复：使用滑动窗口代替按小时分组，避免假警报
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
        """
        从任务数据更新检测器（修复版：使用滑动窗口）
        
        修复说明：
        - 旧版本：按小时分组统计，导致新小时只有少量任务时成功率被锁定
        - 新版本：使用滑动窗口（最近200个任务或30分钟），实时反映系统状态
        """
        if not tasks:
            return
        
        # 按时间排序
        tasks = sorted(tasks, key=lambda t: t.get("timestamp", ""))
        
        # 方法1：使用最近N个任务的滑动窗口（推荐）
        window_size = 200  # 最近200个任务
        recent_tasks = tasks[-window_size:] if len(tasks) > window_size else tasks
        
        # 方法2：使用时间窗口（备选）
        # time_window_minutes = 30
        # cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        # recent_tasks = [t for t in tasks if datetime.fromisoformat(t.get("timestamp", "")) >= cutoff_time]
        
        # 计算累计统计（避免按小时分组）
        total_count = len(recent_tasks)
        success_count = sum(1 for t in recent_tasks if t.get("status") == "completed")
        duration_sum = sum(t.get("duration", 0) for t in recent_tasks)
        cost_sum = sum(t.get("cost", 0) for t in recent_tasks)
        
        # 计算指标
        success_rate = success_count / total_count if total_count > 0 else 0
        avg_duration = duration_sum / total_count if total_count > 0 else 0
        error_rate = 1.0 - success_rate
        avg_cost = cost_sum / total_count if total_count > 0 else 0
        
        # 更新检测器（使用当前时间戳）
        now = datetime.now()
        self.detectors["success_rate"].add_data_point(success_rate, now)
        self.detectors["avg_duration"].add_data_point(avg_duration, now)
        self.detectors["error_rate"].add_data_point(error_rate, now)
        self.detectors["cost"].add_data_point(avg_cost, now)
    
    def get_all_trends(self) -> Dict[str, Dict]:
        """获取所有指标的趋势"""
        return {
            metric: detector.get_summary()
            for metric, detector in self.detectors.items()
        }
    
    def detect_anomalies(self) -> List[Dict]:
        """检测异常（例如：成功率骤降、耗时激增）"""
        anomalies = []
        
        # 检查成功率
        success_summary = self.detectors["success_rate"].get_summary()
        if success_summary["current_value"] is not None:
            if success_summary["current_value"] < 0.5:  # 成功率低于50%
                anomalies.append({
                    "type": "low_success_rate",
                    "severity": "critical",
                    "metric": "success_rate",
                    "value": success_summary["current_value"],
                    "message": f"成功率过低: {success_summary['current_value']*100:.1f}%"
                })
            elif success_summary["trend"] == ChangeDetector.TREND_FALLING:
                anomalies.append({
                    "type": "falling_success_rate",
                    "severity": "warning",
                    "metric": "success_rate",
                    "trend": success_summary["trend"],
                    "confidence": success_summary["confidence"],
                    "message": f"成功率下降趋势 (置信度: {success_summary['confidence']*100:.1f}%)"
                })
        
        # 检查耗时
        duration_summary = self.detectors["avg_duration"].get_summary()
        if duration_summary["current_value"] is not None:
            if duration_summary["current_value"] > 60:  # 平均耗时超过60秒
                anomalies.append({
                    "type": "high_duration",
                    "severity": "warning",
                    "metric": "avg_duration",
                    "value": duration_summary["current_value"],
                    "message": f"平均耗时过高: {duration_summary['current_value']:.1f}秒"
                })
        
        # 检查错误率
        error_summary = self.detectors["error_rate"].get_summary()
        if error_summary["current_value"] is not None:
            if error_summary["current_value"] > 0.3:  # 错误率超过30%
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "critical",
                    "metric": "error_rate",
                    "value": error_summary["current_value"],
                    "message": f"错误率过高: {error_summary['current_value']*100:.1f}%"
                })
        
        return anomalies
