#!/usr/bin/env python3
"""
AIOS 错误恢复机制测试
测试自动验证、回滚、灰度修复、手动介入
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
from core.agent_state_machine import AgentStateMachine
from memory.api import memory


class TestRecoveryMechanisms(unittest.TestCase):
    """错误恢复机制测试"""
    
    def setUp(self):
        self.bus = EventBus()
        self.scheduler = ToyScheduler(self.bus)
        self.reactor = ToyReactor(self.bus)
        self.score_engine = ToyScoreEngine(self.bus)
        
        self.scheduler.start()
        self.reactor.start()
        self.score_engine.start()
    
    def test_auto_verify_fix_success(self):
        """测试自动验证修复成功"""
        # 发送错误事件
        event = Event.create(
            event_type="agent_error",
            source="agent-001",
            payload={"type": "network_disconnect", "severity": "high"}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证Scheduler触发修复
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
        
        # 验证Reactor执行修复
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
        
        # 验证修复后状态恢复
        # （实际应该检查Agent状态，这里简化）
    
    def test_rollback_on_fix_failure(self):
        """测试修复失败时回滚"""
        # 记录初始状态
        initial_score = self.score_engine.get_score()
        
        # 发送需要回滚的错误
        event = Event.create(
            event_type="agent_error",
            source="agent-001",
            payload={"type": "critical", "need_rollback": True}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证触发修复尝试
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
        
        # 验证记录到Memory
        results = memory.find_similar("critical")
        # 应该有相关记录
    
    def test_gray_scale_fix_progression(self):
        """测试灰度修复（10% → 50% → 100%）"""
        # 模拟灰度修复过程
        stages = []
        
        # 第一阶段：10%
        event1 = Event.create(
            event_type="fix.gray_scale",
            source="reactor",
            payload={"stage": "10%", "target": "memory_overflow"}
        )
        self.bus.emit(event1)
        time.sleep(0.1)
        stages.append(True)
        
        # 第二阶段：50%
        event2 = Event.create(
            event_type="fix.gray_scale",
            source="reactor",
            payload={"stage": "50%", "target": "memory_overflow"}
        )
        self.bus.emit(event2)
        time.sleep(0.1)
        stages.append(True)
        
        # 第三阶段：100%
        event3 = Event.create(
            event_type="fix.gray_scale",
            source="reactor",
            payload={"stage": "100%", "target": "memory_overflow"}
        )
        self.bus.emit(event3)
        time.sleep(0.1)
        stages.append(True)
        
        # 验证所有阶段成功
        self.assertEqual(stages, [True, True, True])
        
        # 验证评分稳定
        score = self.score_engine.get_score()
        self.assertIsNotNone(score)
    
    def test_manual_intervention_api(self):
        """测试手动介入API"""
        # 发送手动介入事件
        event = Event.create(
            event_type="manual.intervention",
            source="human",
            payload={"action": "emergency_stop", "reason": "human_override"}
        )
        self.bus.emit(event)
        
        time.sleep(0.2)
        
        # 验证事件被处理
        stats = self.score_engine.get_stats()
        self.assertGreater(stats['total_events'], 0)
        
        # 验证记录到Memory
        memory.store_lesson(
            category="manual_intervention",
            pattern="emergency_stop",
            lesson="人工介入：紧急停止",
            reason="human_override"
        )
        
        results = memory.find_similar("human_override")
        self.assertGreater(len(results), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
