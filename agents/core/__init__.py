"""
AIOS v2.0 - Core Agents
8个核心Agent，职责极致单一
"""

from pathlib import Path
import sys
import os

# 添加workspace到路径
# __file__ = .../aios/agents/core/__init__.py
# parent = .../aios/agents/core
# parent.parent = .../aios/agents
# parent.parent.parent = .../aios
# 我们需要再往上一层到workspace
workspace = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace))

# 直接导入base模块
base_path = workspace / 'aios' / 'agents' / 'base.py'
import importlib.util
spec = importlib.util.spec_from_file_location("base", base_path)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

DispatcherAgent = base.DispatcherAgent
BaseAgent = base.BaseAgent
ServiceAgent = base.ServiceAgent
TaskContext = base.TaskContext

from typing import Dict, Any


# ============================================================
# 1. coder-dispatcher - 代码生成任务分发
# ============================================================
class CoderDispatcher(DispatcherAgent):
    """
    职责：只负责代码生成类任务的拆解与分发
    """
    
    def __init__(self):
        super().__init__(
            agent_id='coder-dispatcher',
            config={
                'routing_rules': {
                    'code_generation': 'code-generator',
                    'code_review': 'code-reviewer',
                    'code_refactor': 'code-refactor',
                    'bug_fix': 'bug-fixer'
                }
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证是否为代码类任务"""
        valid_types = ['code_generation', 'code_review', 'code_refactor', 'bug_fix']
        return context.task_type in valid_types


# ============================================================
# 2. analyst-dispatcher - 数据分析任务分发
# ============================================================
class AnalystDispatcher(DispatcherAgent):
    """
    职责：只负责数据分析/洞察类任务分发
    """
    
    def __init__(self):
        super().__init__(
            agent_id='analyst-dispatcher',
            config={
                'routing_rules': {
                    'pattern_analysis': 'pattern-analyzer',
                    'trend_analysis': 'trend-analyzer',
                    'anomaly_detection': 'anomaly-analyzer',
                    'cost_analysis': 'cost-analyzer'
                }
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证是否为分析类任务"""
        valid_types = ['pattern_analysis', 'trend_analysis', 'anomaly_detection', 'cost_analysis']
        return context.task_type in valid_types


# ============================================================
# 3. monitor-dispatcher - 系统健康监控分发
# ============================================================
class MonitorDispatcher(DispatcherAgent):
    """
    职责：只负责系统健康、异常检测分发
    """
    
    def __init__(self):
        super().__init__(
            agent_id='monitor-dispatcher',
            config={
                'routing_rules': {
                    'health_check': 'health-monitor',
                    'resource_monitor': 'resource-monitor',
                    'error_detection': 'error-detector',
                    'performance_monitor': 'performance-monitor'
                }
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证是否为监控类任务"""
        valid_types = ['health_check', 'resource_monitor', 'error_detection', 'performance_monitor']
        return context.task_type in valid_types


# ============================================================
# 4. task-queue-processor - 纯队列消费引擎
# ============================================================
class TaskQueueProcessor(BaseAgent):
    """
    职责：纯队列消费引擎（FIFO + 优先级）
    """
    
    def __init__(self):
        super().__init__(
            agent_id='task-queue-processor',
            config={
                'max_batch_size': 5,
                'priority_levels': ['high', 'normal', 'low']
            }
        )
        self.queue_file = Path('aios/agent_system/task_queue.jsonl')
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证任务格式"""
        return bool(context.task_id and context.task_type)
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """从队列消费任务并分发"""
        # 实际实现应该读取task_queue.jsonl
        # 这里返回模拟结果
        return {
            'success': True,
            'result': {
                'consumed': 1,
                'dispatched_to': self._route_by_type(context.task_type)
            }
        }
    
    def _route_by_type(self, task_type: str) -> str:
        """根据任务类型路由到对应dispatcher"""
        if 'code' in task_type:
            return 'coder-dispatcher'
        elif 'analysis' in task_type or 'trend' in task_type:
            return 'analyst-dispatcher'
        elif 'monitor' in task_type or 'health' in task_type:
            return 'monitor-dispatcher'
        else:
            return 'default-executor'


# ============================================================
# 5. task-scheduler - 定时任务、依赖调度器
# ============================================================
class TaskScheduler(BaseAgent):
    """
    职责：定时任务、依赖调度器
    """
    
    def __init__(self):
        super().__init__(
            agent_id='task-scheduler',
            config={
                'check_interval_seconds': 60,
                'max_concurrent_tasks': 10
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证调度任务格式"""
        return 'schedule' in context.metadata or 'dependencies' in context.metadata
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """执行调度逻辑"""
        schedule = context.metadata.get('schedule')
        dependencies = context.metadata.get('dependencies', [])
        
        # 检查依赖是否满足
        if dependencies:
            # 实际实现应该检查依赖任务状态
            pass
        
        return {
            'success': True,
            'result': {
                'scheduled': True,
                'next_run': schedule
            }
        }


# ============================================================
# 6. model-router - LLM路由 + 负载均衡 + 成本控制
# ============================================================
class ModelRouter(BaseAgent):
    """
    职责：LLM路由 + 负载均衡 + 成本控制
    """
    
    def __init__(self):
        super().__init__(
            agent_id='model-router',
            config={
                'models': {
                    'fast': 'claude-haiku-4-5',
                    'balanced': 'claude-sonnet-4-6',
                    'powerful': 'claude-opus-4-6'
                },
                'cost_limits': {
                    'daily_max_usd': 50.0
                }
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证模型请求格式"""
        return 'model_requirement' in context.metadata
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """路由到最优模型"""
        requirement = context.metadata.get('model_requirement', 'balanced')
        
        # 根据任务复杂度选择模型
        if context.priority == 'high' or 'complex' in context.description.lower():
            model = self.config['models']['powerful']
        elif 'simple' in context.description.lower():
            model = self.config['models']['fast']
        else:
            model = self.config['models']['balanced']
        
        return {
            'success': True,
            'result': {
                'selected_model': model,
                'reason': f'Based on priority={context.priority}'
            }
        }


# ============================================================
# 7. auto-fixer - LowSuccess regeneration核心（自愈逻辑唯一入口）
# ============================================================
class AutoFixer(BaseAgent):
    """
    职责：LowSuccess regeneration核心（自愈逻辑唯一入口）
    """
    
    def __init__(self):
        super().__init__(
            agent_id='auto-fixer',
            config={
                'regeneration_threshold': 0.75,  # 成功率<75%触发
                'max_retry_attempts': 3
            }
        )
        self.lessons_file = Path('aios/agent_system/lessons.json')
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证失败任务格式"""
        return 'error_type' in context.metadata
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """自愈逻辑：分析失败原因 + 生成修复策略"""
        error_type = context.metadata.get('error_type', 'unknown')
        
        # 生成修复策略
        strategy = self._generate_fix_strategy(error_type)
        
        return {
            'success': True,
            'result': {
                'fix_strategy': strategy,
                'should_retry': True,
                'estimated_success_rate': 0.75
            }
        }
    
    def _generate_fix_strategy(self, error_type: str) -> Dict[str, Any]:
        """根据错误类型生成修复策略"""
        strategies = {
            'timeout': {
                'action': 'increase_timeout',
                'params': {'new_timeout': 120}
            },
            'dependency_error': {
                'action': 'check_dependencies',
                'params': {'verify_versions': True}
            },
            'resource_exhausted': {
                'action': 'optimize_resources',
                'params': {'reduce_batch_size': True}
            }
        }
        return strategies.get(error_type, {'action': 'default_recovery'})


# ============================================================
# 8. dependency-manager - 依赖解析、版本锁定、冲突解决
# ============================================================
class DependencyManager(BaseAgent):
    """
    职责：依赖解析、版本锁定、冲突解决
    """
    
    def __init__(self):
        super().__init__(
            agent_id='dependency-manager',
            config={
                'lock_file': 'aios/agent_system/dependencies.lock',
                'conflict_resolution': 'latest'
            }
        )
    
    def validate_input(self, context: TaskContext) -> bool:
        """验证依赖请求格式"""
        return 'dependencies' in context.metadata
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """解析依赖并检查冲突"""
        dependencies = context.metadata.get('dependencies', [])
        
        # 检查版本冲突
        conflicts = self._check_conflicts(dependencies)
        
        if conflicts:
            # 解决冲突
            resolved = self._resolve_conflicts(conflicts)
            return {
                'success': True,
                'result': {
                    'conflicts_found': len(conflicts),
                    'resolved': resolved
                }
            }
        
        return {
            'success': True,
            'result': {
                'dependencies': dependencies,
                'conflicts': []
            }
        }
    
    def _check_conflicts(self, dependencies: list) -> list:
        """检查依赖冲突"""
        # 实际实现应该检查版本兼容性
        return []
    
    def _resolve_conflicts(self, conflicts: list) -> dict:
        """解决依赖冲突"""
        # 实际实现应该根据策略解决冲突
        return {'strategy': self.config['conflict_resolution']}


# ============================================================
# Agent工厂
# ============================================================
def create_core_agents() -> Dict[str, BaseAgent]:
    """创建所有核心Agent实例"""
    return {
        'coder-dispatcher': CoderDispatcher(),
        'analyst-dispatcher': AnalystDispatcher(),
        'monitor-dispatcher': MonitorDispatcher(),
        'task-queue-processor': TaskQueueProcessor(),
        'task-scheduler': TaskScheduler(),
        'model-router': ModelRouter(),
        'auto-fixer': AutoFixer(),
        'dependency-manager': DependencyManager()
    }


# ============================================================
# 测试代码
# ============================================================
if __name__ == '__main__':
    print("AIOS v2.0 - Core Agents Test\n")
    
    # 创建所有核心Agent
    agents = create_core_agents()
    
    # 测试每个Agent
    for agent_id, agent in agents.items():
        print(f"[TEST] {agent_id}")
        
        # 创建测试任务
        if 'dispatcher' in agent_id:
            task_type = 'code_generation' if 'coder' in agent_id else 'pattern_analysis'
        elif agent_id == 'task-queue-processor':
            task_type = 'code_generation'
        elif agent_id == 'task-scheduler':
            task_type = 'scheduled_task'
        elif agent_id == 'model-router':
            task_type = 'model_request'
        elif agent_id == 'auto-fixer':
            task_type = 'failed_task'
        else:
            task_type = 'dependency_check'
        
        context = TaskContext(
            task_id=f'test-{agent_id}-001',
            task_type=task_type,
            description=f'Test task for {agent_id}',
            priority='normal',
            metadata={
                'schedule': '0 * * * *' if agent_id == 'task-scheduler' else None,
                'model_requirement': 'balanced' if agent_id == 'model-router' else None,
                'error_type': 'timeout' if agent_id == 'auto-fixer' else None,
                'dependencies': ['dep1', 'dep2'] if agent_id == 'dependency-manager' else None
            }
        )
        
        # 执行任务
        result = agent.run(context)
        
        print(f"  Success: {result['success']}")
        print(f"  Latency: {result.get('latency_ms', 0):.2f}ms")
        print(f"  Result: {result.get('result', {})}")
        print()
    
    print("\n[METRICS] All Agents")
    for agent_id, agent in agents.items():
        metrics = agent.get_metrics()
        success_rate = metrics['metrics'].get('success_rate', 0)
        print(f"{agent_id}: {success_rate:.1f}% success rate")
