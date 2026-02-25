"""
Resource Threshold Monitor - 持续时间判定 + 滞回
�?瞬间尖刺"变成"持续异常"

核心思想�?1. 持续时间判定：CPU > 80% 连续 10s 才触�?2. 滞回：触发 80% / 恢复 70%，避免临界点抖动

事件流：
- resource.threshold_candidate
- resource.threshold_confirmed
"""

import time
from pathlib import Path
import sys
from typing import Dict, Optional
from collections import defaultdict

# 添加路径
AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import create_event, EventType
from core.event_bus import emit


class ThresholdMonitor:
    """阈值监控器（持续时�?+ 滞回�?""
    
    def __init__(
        self,
        bus=None,
        cpu_trigger_threshold: float = 80.0,
        cpu_recover_threshold: float = 70.0,
        cpu_duration_seconds: int = 10,
        memory_trigger_threshold: float = 85.0,
        memory_recover_threshold: float = 75.0,
        memory_duration_seconds: int = 30,
        sample_interval: float = 1.0
    ):
        """
        初始化阈值监控器
        
        Args:
            bus: EventBus 实例
            cpu_trigger_threshold: CPU 触发阈值（%�?            cpu_recover_threshold: CPU 恢复阈值（%�?            cpu_duration_seconds: CPU 持续时间（秒�?            memory_trigger_threshold: 内存触发阈值（%�?            memory_recover_threshold: 内存恢复阈值（%�?            memory_duration_seconds: 内存持续时间（秒�?            sample_interval: 采样间隔（秒�?        """
        from core.event_bus import get_event_bus
        self.bus = bus or get_event_bus()
        
        self.cpu_trigger_threshold = cpu_trigger_threshold
        self.cpu_recover_threshold = cpu_recover_threshold
        self.cpu_duration_seconds = cpu_duration_seconds
        
        self.memory_trigger_threshold = memory_trigger_threshold
        self.memory_recover_threshold = memory_recover_threshold
        self.memory_duration_seconds = memory_duration_seconds
        
        self.sample_interval = sample_interval
        
        # 状态跟�?        self.cpu_candidate_start: Optional[float] = None
        self.cpu_confirmed = False
        
        self.memory_candidate_start: Optional[float] = None
        self.memory_confirmed = False
    
    def check_cpu(self, cpu_percent: float):
        """
        检�?CPU 使用�?        
        Args:
            cpu_percent: CPU 使用率（%�?        """
        now = time.time()
        
        # 情况1：已确认，检查是否恢�?        if self.cpu_confirmed:
            if cpu_percent <= self.cpu_recover_threshold:
                # 恢复
                self.cpu_confirmed = False
                self.cpu_candidate_start = None
                self.bus.self.bus.emit(create_event(
                    EventType.RESOURCE_RECOVERED,
                    source="threshold_monitor",
                    resource_type="cpu",
                    value=cpu_percent,
                    threshold=self.cpu_recover_threshold
                ))
            return
        
        # 情况2：候选中，检查是否持�?        if self.cpu_candidate_start is not None:
            if cpu_percent > self.cpu_trigger_threshold:
                # 仍在高位，检查持续时�?                duration = now - self.cpu_candidate_start
                if duration >= self.cpu_duration_seconds:
                    # 确认触发
                    self.cpu_confirmed = True
                    self.bus.self.bus.emit(create_event(
                        EventType.RESOURCE_THRESHOLD_CONFIRMED,
                        source="threshold_monitor",
                        resource_type="cpu",
                        value=cpu_percent,
                        threshold=self.cpu_trigger_threshold,
                        duration=duration
                    ))
            else:
                # 回落，取消候�?                self.cpu_candidate_start = None
            return
        
        # 情况3：正常状态，检查是否开始候�?        if cpu_percent > self.cpu_trigger_threshold:
            # 开始候�?            self.cpu_candidate_start = now
            self.bus.self.bus.emit(create_event(
                EventType.RESOURCE_THRESHOLD_CANDIDATE,
                source="threshold_monitor",
                resource_type="cpu",
                value=cpu_percent,
                threshold=self.cpu_trigger_threshold
            ))
    
    def check_memory(self, memory_percent: float):
        """
        检查内存使用率
        
        Args:
            memory_percent: 内存使用率（%�?        """
        now = time.time()
        
        # 情况1：已确认，检查是否恢�?        if self.memory_confirmed:
            if memory_percent <= self.memory_recover_threshold:
                # 恢复
                self.memory_confirmed = False
                self.memory_candidate_start = None
                self.bus.emit(create_event(
                    EventType.RESOURCE_RECOVERED,
                    source="threshold_monitor",
                    resource_type="memory",
                    value=memory_percent,
                    threshold=self.memory_recover_threshold
                ))
            return
        
        # 情况2：候选中，检查是否持�?        if self.memory_candidate_start is not None:
            if memory_percent > self.memory_trigger_threshold:
                # 仍在高位，检查持续时�?                duration = now - self.memory_candidate_start
                if duration >= self.memory_duration_seconds:
                    # 确认触发
                    self.memory_confirmed = True
                    self.bus.emit(create_event(
                        EventType.RESOURCE_THRESHOLD_CONFIRMED,
                        source="threshold_monitor",
                        resource_type="memory",
                        value=memory_percent,
                        threshold=self.memory_trigger_threshold,
                        duration=duration
                    ))
            else:
                # 回落，取消候�?                self.memory_candidate_start = None
            return
        
        # 情况3：正常状态，检查是否开始候�?        if memory_percent > self.memory_trigger_threshold:
            # 开始候�?            self.memory_candidate_start = now
            self.bus.emit(create_event(
                EventType.RESOURCE_THRESHOLD_CANDIDATE,
                source="threshold_monitor",
                resource_type="memory",
                value=memory_percent,
                threshold=self.memory_trigger_threshold
            ))
    
    def get_status(self) -> dict:
        """获取当前状�?""
        return {
            "cpu": {
                "confirmed": self.cpu_confirmed,
                "candidate": self.cpu_candidate_start is not None,
                "candidate_duration": time.time() - self.cpu_candidate_start if self.cpu_candidate_start else 0,
                "trigger_threshold": self.cpu_trigger_threshold,
                "recover_threshold": self.cpu_recover_threshold,
                "required_duration": self.cpu_duration_seconds
            },
            "memory": {
                "confirmed": self.memory_confirmed,
                "candidate": self.memory_candidate_start is not None,
                "candidate_duration": time.time() - self.memory_candidate_start if self.memory_candidate_start else 0,
                "trigger_threshold": self.memory_trigger_threshold,
                "recover_threshold": self.memory_recover_threshold,
                "required_duration": self.memory_duration_seconds
            }
        }


# 全局单例
_threshold_monitor: Optional[ThresholdMonitor] = None


def get_threshold_monitor() -> ThresholdMonitor:
    """获取全局阈值监控器实例"""
    global _threshold_monitor
    if _threshold_monitor is None:
        _threshold_monitor = ThresholdMonitor()
    return _threshold_monitor


# CLI 工具
if __name__ == "__main__":
    import sys
    import json
    
    monitor = get_threshold_monitor()
    
    if len(sys.argv) < 2:
        print("用法: python -m aios.core.threshold_monitor status")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        status = monitor.get_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)

