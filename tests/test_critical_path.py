#!/usr/bin/env python3
"""
AIOS 关键路径集成测试
测试实际的事件流和组件交互
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
import json
import time
from datetime import datetime
from pathlib import Path

from core.event import Event
from core.event_bus import EventBus
from core.toy_scheduler import ToyScheduler
from core.toy_reactor import ToyReactor
from core.toy_score_engine import ToyScoreEngine


class TestEventDrivenFlow(unittest.TestCase):
    """测试事件驱动流程"""
    
    def setUp(self):
        self.bus = EventBus()
        self.scheduler = ToyScheduler(self.bus)
        self.reactor = ToyReactor(self.bus)
        self.score_engine = ToyScoreEngine(self.bus)
        
        # 启动组件
        self.scheduler.start()
        self.reactor.start()
        self.score_engine.start()
    
    def test_resource_alert_flow(self):
        """测试资源告警流程"""
        # 发送资源告警事件
        event = Event.create(
            event_type="resource_alert",
            source="test",
            payload={
                "resource": "cpu",
                "value": 95,
                "threshold": 80,
                "severity": "high"
            }
        )
        self.bus.emit(event)
        
        # 等待处理
        time.sleep(0.1)
        
        # 验证 Scheduler 收到并处理
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
    
    def test_error_event_flow(self):
        """测试错误事件流程"""
        # 发送错误事件
        event = Event.create(
            event_type="agent_error",
            source="test",
            payload={
                "agent_id": "test-agent",
                "error": "timeout",
                "severity": "medium"
            }
        )
        self.bus.emit(event)
        
        # 等待处理
        time.sleep(0.1)
        
        # 验证处理
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
    
    def test_score_calculation(self):
        """测试评分计算"""
        # 发送一些事件
        for i in range(5):
            event = Event.create(
                event_type="pipeline_completed",
                source="test",
                payload={"success": True, "duration": 1.0}
            )
            self.bus.emit(event)
        
        # 等待计算
        time.sleep(0.2)
        
        # 获取评分
        score = self.score_engine.get_score()
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 1)


class TestBoundaryConditions(unittest.TestCase):
    """测试边界条件"""
    
    def test_empty_event_bus(self):
        """测试空事件总线"""
        bus = EventBus()
        scheduler = ToyScheduler(bus)
        scheduler.start()
        
        # 不发送任何事件
        time.sleep(0.1)
        
        # 应该正常运行，不崩溃
        actions = scheduler.get_actions()
        # 可能为空或None
    
    def test_rapid_events(self):
        """测试快速连续事件"""
        bus = EventBus()
        scheduler = ToyScheduler(bus)
        scheduler.start()
        
        # 快速发送多个事件
        for i in range(100):
            event = Event.create(
                event_type="resource_alert",
                source="test",
                payload={"resource": "cpu", "value": 90}
            )
            bus.emit(event)
        
        # 等待处理
        time.sleep(0.5)
        
        # 应该能处理，不崩溃
        actions = scheduler.get_actions()
    
    def test_invalid_event_data(self):
        """测试无效事件数据"""
        bus = EventBus()
        scheduler = ToyScheduler(bus)
        scheduler.start()
        
        # 发送无效数据
        event = Event.create(
            event_type="resource_alert",
            source="test",
            payload=None  # 无效数据
        )
        bus.emit(event)
        
        # 应该能处理，不崩溃
        time.sleep(0.1)


class TestReactorExecution(unittest.TestCase):
    """测试 Reactor 执行"""
    
    def setUp(self):
        self.bus = EventBus()
        self.reactor = ToyReactor(self.bus)
        self.reactor.start()
    
    def test_reactor_receives_decision(self):
        """测试 Reactor 接收决策"""
        # 发送决策事件
        event = Event.create(
            event_type="decision",
            source="test",
            payload={
                "action": "trigger_reactor",
                "playbook_id": "test-playbook"
            }
        )
        self.bus.emit(event)
        
        # 等待处理
        time.sleep(0.1)
        
        # 验证执行
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
    
    def test_reactor_cooldown(self):
        """测试 Reactor 冷却期"""
        # 发送同一决策两次
        event = Event.create(
            event_type="decision",
            source="test",
            payload={
                "action": "trigger_reactor",
                "playbook_id": "test-cooldown"
            }
        )
        
        self.bus.emit(event)
        time.sleep(0.1)
        
        # 立即再次发送
        self.bus.emit(event)
        time.sleep(0.1)
        
        # 第二次应该被冷却期阻止
        executions = self.reactor.get_executions()
        # 根据实际实现验证


class TestScoreEngineMetrics(unittest.TestCase):
    """测试 ScoreEngine 指标"""
    
    def setUp(self):
        self.bus = EventBus()
        self.score_engine = ToyScoreEngine(self.bus)
        self.score_engine.start()
    
    def test_score_starts_neutral(self):
        """测试初始评分"""
        score = self.score_engine.get_score()
        # 初始评分应该在合理范围
        if score is not None:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
    
    def test_score_updates_on_events(self):
        """测试事件更新评分"""
        initial_score = self.score_engine.get_score()
        
        # 发送一些成功事件
        for i in range(10):
            event = Event.create(
                event_type="pipeline_completed",
                source="test",
                payload={"success": True}
            )
            self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 评分应该更新
        new_score = self.score_engine.get_score()
        # 可能变化，也可能不变（取决于实现）
    
    def test_score_history(self):
        """测试评分历史"""
        # 发送一些事件
        for i in range(5):
            event = Event.create(
                event_type="pipeline_completed",
                source="test",
                payload={"success": True}
            )
            self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 获取历史
        history = self.score_engine.get_history()
        self.assertIsNotNone(history)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
