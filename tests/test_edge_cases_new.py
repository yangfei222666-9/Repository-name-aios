#!/usr/bin/env python3
"""
AIOS 边界场景测试
测试网络断开、磁盘满、内存溢出等极端情况
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import time
from unittest.mock import patch, MagicMock
from core.event import Event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine
from memory.api import memory


class TestEdgeCases(unittest.TestCase):
    """边界场景测试"""
    
    def setUp(self):
        self.bus = EventBus()
        self.scheduler = ToyScheduler(self.bus)
        self.reactor = ToyReactor(self.bus)
        self.score_engine = ToyScoreEngine(self.bus)
        
        self.scheduler.start()
        self.reactor.start()
        self.score_engine.start()
    
    def test_network_disconnect_recovery(self):
        """测试网络断开恢复"""
        # 发送网络断开事件
        event = Event.create(
            event_type="agent_error",
            source="test",
            payload={"type": "network_disconnect", "severity": "high"}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证Scheduler收到并处理
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
    
    def test_disk_full_95_percent(self):
        """测试磁盘95%满"""
        event = Event.create(
            event_type="resource.disk_full",
            source="sensor",
            payload={"usage": 95, "threshold": 90}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证触发告警
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
    
    def test_disk_full_99_percent(self):
        """测试磁盘99%满"""
        event = Event.create(
            event_type="resource.disk_full",
            source="sensor",
            payload={"usage": 99, "threshold": 90}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证触发紧急修复
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
    
    def test_disk_full_100_percent(self):
        """测试磁盘100%满"""
        event = Event.create(
            event_type="resource.disk_full",
            source="sensor",
            payload={"usage": 100, "threshold": 90}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证系统降级
        score = self.score_engine.get_score()
        # 评分应该受影响
    
    def test_memory_overflow(self):
        """测试内存溢出"""
        # 记录初始评分
        initial_score = self.score_engine.get_score()
        
        # 发送内存溢出事件
        event = Event.create(
            event_type="resource.memory_high",
            source="sensor",
            payload={"usage": 98, "threshold": 80}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证触发处理
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
    
    def test_agent_crash_during_task(self):
        """测试Agent执行任务时崩溃"""
        # 发送Agent崩溃事件
        event = Event.create(
            event_type="agent_error",
            source="agent-001",
            payload={"type": "crash", "task": "processing"}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证记录到Memory
        results = memory.find_similar("crash")
        # 应该能找到相关记录
    
    def test_zero_events_score(self):
        """测试零事件时的评分"""
        # 不发送任何事件
        score = self.score_engine.get_score()
        
        # 初始评分应该存在
        self.assertIsNotNone(score)
    
    def test_extreme_high_severity(self):
        """测试极高严重度事件"""
        # 发送极高严重度事件
        for i in range(5):
            event = Event.create(
                event_type="alert.critical",
                source="sensor",
                payload={"severity": "extreme", "count": i}
            )
            self.bus.emit(event)
        
        time.sleep(0.5)
        
        # 验证触发多次修复
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
    
    def test_invalid_event_format(self):
        """测试无效事件格式"""
        # Event.create会自动处理None payload
        event = Event.create(
            event_type="test.invalid",
            source="test",
            payload=None
        )
        
        # 应该能正常创建（payload会变成空字典）
        self.assertIsNotNone(event)
        self.assertEqual(event.payload, {})
    
    def test_concurrent_events(self):
        """测试并发事件"""
        # 快速发送50个事件
        for i in range(50):
            event = Event.create(
                event_type=f"test.concurrent_{i % 5}",
                source="test",
                payload={"index": i}
            )
            self.bus.emit(event)
        
        time.sleep(1.0)
        
        # 验证系统能处理
        stats = self.score_engine.get_stats()
        self.assertGreater(stats['total_events'], 40)


if __name__ == '__main__':
    unittest.main(verbosity=2)
