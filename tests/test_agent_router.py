import unittest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.router.agent_router import route_task, TaskIndicators

class TestRouter(unittest.TestCase):
    def test_kun_gua_slow(self):
        """测试坤卦 + 高复杂度 → slow"""
        ind: TaskIndicators = {
            "needs_code": True,
            "high_risk": True,
            "est_lines": 180,
            "dependencies": 5,
            "requires_reasoning": True
        }
        model = route_task("task-001", "实现 LowSuccess_Agent Phase 3 重生逻辑", ind)
        self.assertEqual(model, "slow")  # 坤卦 + 高复杂度
    
    def test_simple_fast(self):
        """测试简单任务 → fast"""
        ind: TaskIndicators = {
            "needs_code": False,
            "high_risk": False,
            "est_lines": 10,
            "dependencies": 0
        }
        model = route_task("task-002", "简单日志记录", ind)
        self.assertEqual(model, "fast")
    
    def test_medium_complexity(self):
        """测试中等复杂度任务"""
        ind: TaskIndicators = {
            "needs_code": True,
            "high_risk": False,
            "est_lines": 60,
            "dependencies": 2,
            "requires_reasoning": False
        }
        model = route_task("task-003", "重构 scheduler.py 的日志模块", ind)
        # 中等复杂度，可能是 fast 或 slow，取决于 Evolution Score
        self.assertIn(model, ["fast", "slow"])

if __name__ == "__main__":
    unittest.main()
