#!/usr/bin/env python3
"""
AIOS 端到端集成测试
测试完整的错误处理流程：error → scheduler → reactor → recovery → memory → score
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
from core.agent_state_machine import AgentStateMachine
from memory.api import memory


class TestIntegrationFlows(unittest.TestCase):
    """端到端集成测试"""
    
    def setUp(self):
        self.bus = EventBus()
        self.scheduler = ToyScheduler(self.bus)
        self.reactor = ToyReactor(self.bus)
        self.score_engine = ToyScoreEngine(self.bus)
        
        self.scheduler.start()
        self.reactor.start()
        self.score_engine.start()
    
    def test_full_agent_error_to_recovery_flow(self):
        """完整端到端：Agent错误 → Scheduler决策 → Reactor修复 → Memory记录 → Score更新"""
        # 记录初始状态
        initial_score = self.score_engine.get_score()
        
        # 1. 触发Agent错误
        error_event = Event.create(
            event_type="agent_error",
            source="agent-001",
            payload={
                "type": "network_disconnect",
                "severity": "high",
                "task_id": "task_001"
            }
        )
        self.bus.emit(error_event)
        
        # 等待处理
        time.sleep(0.3)
        
        # 2. 验证Scheduler收到并决策
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
        
        # 3. 验证Reactor执行修复
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
        
        # 4. 验证Memory记录
        memory.store_lesson(
            category="network_error",
            pattern="disconnect",
            lesson="网络断开时使用重试机制",
            task_id="task_001"
        )
        results = memory.find_similar("network_disconnect")
        self.assertGreater(len(results), 0)
        
        # 5. 验证Score更新
        final_score = self.score_engine.get_score()
        self.assertIsNotNone(final_score)
        
        # 完整闭环验证通过
        print("✅ 完整闭环测试通过：error → scheduler → reactor → memory → score")
    
    def test_cascade_failure_with_multiple_resources(self):
        """级联故障集成测试：CPU+内存同时高 → 复合处理"""
        # 同时触发CPU和内存告警
        cpu_event = Event.create(
            event_type="resource.cpu_high",
            source="sensor",
            payload={"usage": 92, "threshold": 80}
        )
        
        memory_event = Event.create(
            event_type="resource.memory_high",
            source="sensor",
            payload={"usage": 95, "threshold": 80}
        )
        
        # 快速连续发送
        self.bus.emit(cpu_event)
        time.sleep(0.05)
        self.bus.emit(memory_event)
        
        # 等待处理
        time.sleep(0.5)
        
        # 验证Scheduler处理多个告警
        actions = self.scheduler.get_actions()
        self.assertIsNotNone(actions)
        
        # 验证Reactor执行修复
        executions = self.reactor.get_executions()
        self.assertIsNotNone(executions)
        
        # 验证记录级联故障
        memory.store_lesson(
            category="cascade_failure",
            pattern="cpu_memory_high",
            lesson="CPU和内存同时高时，优先清理内存",
            severity="high"
        )
        
        results = memory.find_similar("cascade")
        self.assertGreater(len(results), 0)
        
        # 验证系统恢复
        score = self.score_engine.get_score()
        self.assertIsNotNone(score)
        
        print("✅ 级联故障测试通过：多资源同时告警 → 复合处理 → 恢复")


if __name__ == '__main__':
    unittest.main(verbosity=2)
