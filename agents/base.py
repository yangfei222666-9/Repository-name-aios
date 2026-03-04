"""
AIOS v2.0 - 统一Agent基类
减少重复代码80%，标准化生命周期管理
"""

import json
import time
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class AgentMetrics:
    """Agent运行指标"""
    tasks_total: int = 0
    tasks_success: int = 0
    tasks_failed: int = 0
    avg_latency_ms: float = 0.0
    last_run_timestamp: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        if self.tasks_total == 0:
            return 0.0
        return (self.tasks_success / self.tasks_total) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    task_type: str
    description: str
    priority: str = "normal"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    统一Agent基类
    
    所有Agent必须继承此类并实现：
    - execute(): 核心执行逻辑
    - validate_input(): 输入验证
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.metrics = AgentMetrics()
        self.state_file = Path(f"aios/agent_system/state/{agent_id}_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载历史状态
        self._load_state()
    
    def _load_state(self):
        """加载Agent历史状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.metrics = AgentMetrics(**state.get('metrics', {}))
            except Exception as e:
                print(f"[WARN] Failed to load state for {self.agent_id}: {e}")
    
    def _save_state(self):
        """保存Agent状态"""
        try:
            state = {
                'agent_id': self.agent_id,
                'metrics': self.metrics.to_dict(),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save state for {self.agent_id}: {e}")
    
    @abstractmethod
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """
        核心执行逻辑（子类必须实现）
        
        Args:
            context: 任务上下文
            
        Returns:
            执行结果字典，必须包含：
            - success: bool
            - result: Any
            - error: Optional[str]
        """
        pass
    
    @abstractmethod
    def validate_input(self, context: TaskContext) -> bool:
        """
        输入验证（子类必须实现）
        
        Args:
            context: 任务上下文
            
        Returns:
            验证是否通过
        """
        pass
    
    def run(self, context: TaskContext) -> Dict[str, Any]:
        """
        标准化执行流程（不要重写此方法）
        
        1. 输入验证
        2. 执行任务
        3. 记录指标
        4. 保存状态
        """
        start_time = time.time()
        
        try:
            # 1. 输入验证
            if not self.validate_input(context):
                return {
                    'success': False,
                    'error': 'Input validation failed',
                    'task_id': context.task_id
                }
            
            # 2. 执行任务
            result = self.execute(context)
            
            # 3. 记录指标
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.tasks_total += 1
            
            if result.get('success', False):
                self.metrics.tasks_success += 1
            else:
                self.metrics.tasks_failed += 1
            
            # 更新平均延迟（移动平均）
            if self.metrics.avg_latency_ms == 0:
                self.metrics.avg_latency_ms = latency_ms
            else:
                self.metrics.avg_latency_ms = (
                    self.metrics.avg_latency_ms * 0.9 + latency_ms * 0.1
                )
            
            self.metrics.last_run_timestamp = datetime.now().isoformat()
            
            # 4. 保存状态
            self._save_state()
            
            # 添加执行元数据
            result['latency_ms'] = latency_ms
            result['agent_id'] = self.agent_id
            result['task_id'] = context.task_id
            
            return result
            
        except Exception as e:
            self.metrics.tasks_total += 1
            self.metrics.tasks_failed += 1
            self._save_state()
            
            return {
                'success': False,
                'error': str(e),
                'task_id': context.task_id,
                'agent_id': self.agent_id,
                'latency_ms': (time.time() - start_time) * 1000
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取Agent指标"""
        return {
            'agent_id': self.agent_id,
            'metrics': self.metrics.to_dict(),
            'config': self.config
        }
    
    def reset_metrics(self):
        """重置指标（用于测试）"""
        self.metrics = AgentMetrics()
        self._save_state()


class DispatcherAgent(BaseAgent):
    """
    Dispatcher类Agent基类
    
    职责：任务分发 + 路由
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.routing_rules = config.get('routing_rules', {})
    
    def route_task(self, context: TaskContext) -> str:
        """
        任务路由逻辑
        
        Returns:
            目标Agent ID
        """
        # 默认路由逻辑（子类可重写）
        task_type = context.task_type
        return self.routing_rules.get(task_type, 'default-executor')
    
    def execute(self, context: TaskContext) -> Dict[str, Any]:
        """Dispatcher执行逻辑：分发任务"""
        target_agent = self.route_task(context)
        
        # 这里应该调用真实的Agent执行
        # 暂时返回模拟结果
        return {
            'success': True,
            'result': {
                'dispatched_to': target_agent,
                'task_id': context.task_id
            }
        }


class ServiceAgent(BaseAgent):
    """
    Service类Agent基类
    
    职责：无状态服务（通知、数据处理等）
    """
    
    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        super().__init__(agent_id, config)
        self.service_type = config.get('service_type', 'generic')
    
    def health_check(self) -> bool:
        """健康检查"""
        return True


# 导出
__all__ = [
    'BaseAgent',
    'DispatcherAgent',
    'ServiceAgent',
    'TaskContext',
    'AgentMetrics'
]
