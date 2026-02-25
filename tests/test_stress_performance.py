#!/usr/bin/env python3
"""
AIOS 压力和性能测试
测试高并发、性能回归
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import time
from core.event import Event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine
from memory.api import memory


class TestStressPerformance(unittest.TestCase):
    """压力和性能测试"""
    
    def setUp(self):
        self.bus = EventBus()
        self.scheduler = ToyScheduler(self.bus)
        self.reactor = ToyReactor(self.bus)
        self.score_engine = ToyScoreEngine(self.bus)
        
        self.scheduler.start()
        self.reactor.start()
        self.score_engine.start()
    
    def test_1000_events_stress(self):
        """压力测试：1000个事件快速发送"""
        start_time = time.time()
        
        # 快速发送1000个事件
        for i in range(1000):
            event = Event.create(
                event_type=f"stress.test_{i % 10}",
                source="stress_test",
                payload={"id": i, "severity": "medium"}
            )
            self.bus.emit(event)
        
        # 等待处理
        time.sleep(2.0)
        
        duration = time.time() - start_time
        events_per_sec = 1000 / duration
        
        # 验证吞吐量
        print(f"吞吐量: {events_per_sec:.2f} events/sec")
        self.assertGreater(events_per_sec, 100)  # 至少100 events/sec
        
        # 验证系统稳定
        stats = self.score_engine.get_stats()
        self.assertGreater(stats['total_events'], 900)  # 至少处理了90%
        
        # 验证熔断器未触发
        # （实际应该检查熔断器状态）
        
        print("✅ 压力测试通过：1000个事件，系统稳定")
    
    def test_performance_regression_score_calculation(self):
        """性能回归测试：评分计算性能"""
        # 预热
        for _ in range(10):
            self.score_engine.get_score()
        
        # 性能测试
        iterations = 500
        start = time.perf_counter()
        
        for _ in range(iterations):
            score = self.score_engine.get_score()
        
        elapsed_ms = (time.perf_counter() - start) * 1000 / iterations
        
        # 验证性能
        print(f"平均计算时间: {elapsed_ms:.3f}ms")
        self.assertLess(elapsed_ms, 10.0)  # 单次计算必须<10ms
        
        # 验证评分合理
        final_score = self.score_engine.get_score()
        self.assertIsNotNone(final_score)
        self.assertGreaterEqual(final_score, 0.0)
        self.assertLessEqual(final_score, 1.0)
        
        print("✅ 性能回归测试通过：评分计算<10ms")


if __name__ == '__main__':
    unittest.main(verbosity=2)
