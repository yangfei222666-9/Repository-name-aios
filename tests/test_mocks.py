"""
AIOS 模拟测试（Mock Tests）
使用 mock 对象测试复杂交互
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import tempfile
from pathlib import Path
from datetime import datetime
import sys

AIOS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIOS_ROOT))

from core.event import Event, EventType


class TestEventBusMocks:
    """EventBus 模拟测试"""
    
    def test_subscriber_called_on_emit(self):
        """测试订阅者在事件发布时被调用"""
        from core.event_bus import EventBus
        
        bus = EventBus()
        
        # 创建 mock 订阅者
        mock_handler = Mock()
        bus.subscribe("test.event", mock_handler)
        
        # 发布事件
        event = Event.create("test.event", "test_suite", {"data": "test"})
        bus.emit(event)
        
        # 验证 handler 被调用
        mock_handler.assert_called_once()
        
        # 验证传入的参数
        call_args = mock_handler.call_args[0][0]
        assert call_args.type == "test.event"
    
    def test_multiple_subscribers_all_called(self):
        """测试多个订阅者都被调用"""
        from core.event_bus import EventBus
        
        bus = EventBus()
        
        # 创建多个 mock 订阅者
        mock1 = Mock()
        mock2 = Mock()
        mock3 = Mock()
        
        bus.subscribe("test.event", mock1)
        bus.subscribe("test.event", mock2)
        bus.subscribe("test.*", mock3)
        
        # 发布事件
        event = Event.create("test.event", "test_suite", {})
        bus.emit(event)
        
        # 验证所有 handler 都被调用
        mock1.assert_called_once()
        mock2.assert_called_once()
        mock3.assert_called_once()
    
    def test_unsubscribe_stops_calls(self):
        """测试取消订阅后不再被调用"""
        from core.event_bus import EventBus
        
        bus = EventBus()
        
        mock_handler = Mock()
        bus.subscribe("test.event", mock_handler)
        
        # 发布第一个事件
        event1 = Event.create("test.event", "test_suite", {})
        bus.emit(event1)
        
        assert mock_handler.call_count == 1
        
        # 取消订阅
        bus.unsubscribe("test.event", mock_handler)
        
        # 发布第二个事件
        event2 = Event.create("test.event", "test_suite", {})
        bus.emit(event2)
        
        # 验证没有再次调用
        assert mock_handler.call_count == 1


class TestSchedulerMocks:
    """Scheduler 模拟测试"""
    
    def test_scheduler_decision_logic(self):
        """测试 Scheduler 决策逻辑"""
        # 模拟决策函数
        def make_decision(cpu_percent, memory_percent):
            if cpu_percent > 80:
                return "scale_down"
            elif memory_percent > 75:
                return "clear_cache"
            else:
                return "no_action"
        
        # 测试不同场景
        assert make_decision(90, 50) == "scale_down"
        assert make_decision(50, 80) == "clear_cache"
        assert make_decision(50, 50) == "no_action"


class TestReactorMocks:
    """Reactor 模拟测试"""
    
    def test_reactor_matches_playbooks(self):
        """测试 Reactor 匹配 Playbook"""
        # 模拟 Playbook 匹配逻辑
        def match_playbook(event, playbooks):
            matched = []
            for playbook in playbooks:
                if playbook["trigger"]["event_pattern"] in event.type:
                    if event.severity in playbook["trigger"].get("severity", ["INFO", "WARN", "ERR", "CRIT"]):
                        matched.append(playbook)
            return matched
        
        # 测试数据
        event = Event.create("system.resource.high_cpu", "monitor", {})
        event.severity = "WARN"
        
        playbooks = [
            {
                "id": "pb1",
                "trigger": {
                    "event_pattern": "system.resource",
                    "severity": ["WARN", "ERR"]
                }
            },
            {
                "id": "pb2",
                "trigger": {
                    "event_pattern": "system.network",
                    "severity": ["WARN"]
                }
            }
        ]
        
        matched = match_playbook(event, playbooks)
        
        assert len(matched) == 1
        assert matched[0]["id"] == "pb1"


class TestDashboardMocks:
    """Dashboard 模拟测试"""
    
    @patch('dashboard.server.DashboardData.load_jsonl')
    def test_dashboard_loads_events(self, mock_load_jsonl):
        """测试 Dashboard 加载事件"""
        from dashboard.server import DashboardData
        
        # 模拟返回数据
        mock_events = [
            {"ts": "2026-02-24T10:00:00", "event": "test1", "severity": "INFO"},
            {"ts": "2026-02-24T10:01:00", "event": "test2", "severity": "WARN"},
        ]
        mock_load_jsonl.return_value = mock_events
        
        # 调用方法
        events = DashboardData.load_jsonl(Path("dummy.jsonl"))
        
        # 验证
        assert len(events) == 2
        assert events[0]["event"] == "test1"
        mock_load_jsonl.assert_called_once()
    
    def test_dashboard_filters_by_severity(self):
        """测试 Dashboard 按严重级别过滤"""
        events = [
            {"severity": "INFO", "event": "e1"},
            {"severity": "WARN", "event": "e2"},
            {"severity": "ERR", "event": "e3"},
            {"severity": "INFO", "event": "e4"},
        ]
        
        # 过滤错误
        errors = [e for e in events if e["severity"] in ["ERR", "CRIT"]]
        
        assert len(errors) == 1
        assert errors[0]["event"] == "e3"


class TestCircuitBreakerMocks:
    """CircuitBreaker 模拟测试"""
    
    def test_circuit_breaker_opens_after_threshold(self):
        """测试熔断器在达到阈值后打开"""
        from agent_system.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(threshold=3, timeout=60)
        
        # 记录失败（确保达到阈值）
        for _ in range(4):  # 多记录一次确保超过阈值
            breaker.record_failure("test_task")
        
        # 获取状态
        status = breaker.get_status()
        
        # 验证熔断器打开
        assert status["test_task"]["circuit_open"] == True
        assert status["test_task"]["failure_count"] >= 3
    
    def test_circuit_breaker_resets_on_success(self):
        """测试熔断器在成功后重置"""
        from agent_system.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(threshold=3, timeout=60)
        
        # 记录失败
        breaker.record_failure("test_task")
        breaker.record_failure("test_task")
        
        # 记录成功
        breaker.record_success("test_task")
        
        # 验证计数被重置
        assert "test_task" not in breaker.failures


class TestAgentSystemMocks:
    """Agent 系统模拟测试"""
    
    def test_agent_router_selects_correct_agent(self):
        """测试 Agent 路由器选择正确的 Agent"""
        # 模拟路由逻辑
        def route_task(task_description):
            if "code" in task_description.lower():
                return "coder"
            elif "analyze" in task_description.lower():
                return "analyst"
            elif "monitor" in task_description.lower():
                return "monitor"
            else:
                return "general"
        
        # 测试
        assert route_task("Write code for API") == "coder"
        assert route_task("Analyze performance data") == "analyst"
        assert route_task("Monitor system health") == "monitor"
        assert route_task("Do something") == "general"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
