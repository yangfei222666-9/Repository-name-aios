#!/usr/bin/env python3
"""
AIOS Scheduler - 自动调度核心
监控 → 判断 → 触发 → 修复 → 验证 → 更新评分
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from event_bus import get_event_bus, EventType, emit

AIOS_ROOT = Path(__file__).parent

class Scheduler:
    """AIOS 调度核心"""
    
    # 允许调用 Scheduler 的模块白名单
    ALLOWED_CALLERS = {
        'event_bus',
        'reactor_auto_trigger',
        'heartbeat_runner_optimized',
        'scheduler',  # 自己
        '__main__',  # 直接运行
    }
    
    def __init__(self):
        self.event_bus = get_event_bus()
        self.running = False
        self.tasks = []
        self.agents = {}
        
        # 订阅关键事件
        self._setup_listeners()
    
    def _check_caller_permission(self) -> None:
        """
        检查调用者权限
        
        Raises:
            PermissionError: 调用者不在白名单中
        """
        import inspect
        
        # 获取调用栈
        frame = inspect.currentframe()
        if frame is None:
            return  # 无法获取调用栈，跳过检查
        
        try:
            # 向上查找调用者
            caller_frame = frame.f_back.f_back  # 跳过 _check_caller_permission 和当前方法
            if caller_frame is None:
                return
            
            # 获取调用者模块名
            caller_module = inspect.getmodule(caller_frame)
            if caller_module is None:
                return
            
            module_name = caller_module.__name__.split('.')[-1]
            
            # 检查白名单
            if module_name not in self.ALLOWED_CALLERS:
                raise PermissionError(
                    f"Module '{module_name}' is not allowed to call Scheduler. "
                    f"Allowed: {', '.join(self.ALLOWED_CALLERS)}"
                )
        finally:
            del frame
    
    def _setup_listeners(self):
        """设置事件监听器"""
        # 监听资源事件
        self.event_bus.subscribe(EventType.RESOURCE_SPIKE, self._handle_resource_spike)
        self.event_bus.subscribe(EventType.RESOURCE_CRITICAL, self._handle_resource_critical)
        
        # 监听任务事件
        self.event_bus.subscribe(EventType.TASK_FAILED, self._handle_task_failed)
        self.event_bus.subscribe(EventType.TASK_TIMEOUT, self._handle_task_timeout)
        
        # 监听 Agent 事件
        self.event_bus.subscribe(EventType.AGENT_DEGRADED, self._handle_agent_degraded)
        self.event_bus.subscribe(EventType.AGENT_FAILED, self._handle_agent_failed)
    
    def _handle_resource_spike(self, event: Dict):
        """处理资源峰值"""
        data = event['data']
        resource = data.get('resource')
        value = data.get('value')
        
        print(f"⚠️ 资源峰值: {resource} = {value}%")
        
        # 决策：降低并发
        if value > 80:
            emit(EventType.REACTOR_TRIGGERED, {
                "reason": f"{resource}_high",
                "action": "reduce_concurrency",
                "value": value
            })
    
    def _handle_resource_critical(self, event: Dict):
        """处理资源临界"""
        data = event['data']
        resource = data.get('resource')
        
        print(f"🚨 资源临界: {resource}")
        
        # 决策：暂停非关键任务
        emit(EventType.REACTOR_TRIGGERED, {
            "reason": f"{resource}_critical",
            "action": "pause_non_critical_tasks"
        })
    
    def _handle_task_failed(self, event: Dict):
        """处理任务失败"""
        data = event['data']
        task_id = data.get('task_id')
        error = data.get('error')
        
        print(f"❌ 任务失败: {task_id} - {error}")
        
        # 决策：重试或降级
        emit(EventType.REACTOR_TRIGGERED, {
            "reason": "task_failed",
            "action": "retry_or_degrade",
            "task_id": task_id
        })
    
    def _handle_task_timeout(self, event: Dict):
        """处理任务超时"""
        data = event['data']
        task_id = data.get('task_id')
        
        print(f"⏱️ 任务超时: {task_id}")
        
        # 决策：取消并重新调度
        emit(EventType.REACTOR_TRIGGERED, {
            "reason": "task_timeout",
            "action": "cancel_and_reschedule",
            "task_id": task_id
        })
    
    def _handle_agent_degraded(self, event: Dict):
        """处理 Agent 降级"""
        data = event['data']
        agent_id = data.get('agent_id')
        
        print(f"⚠️ Agent 降级: {agent_id}")
        
        # 决策：减少负载
        emit(EventType.REACTOR_TRIGGERED, {
            "reason": "agent_degraded",
            "action": "reduce_agent_load",
            "agent_id": agent_id
        })
    
    def _handle_agent_failed(self, event: Dict):
        """处理 Agent 失败"""
        data = event['data']
        agent_id = data.get('agent_id')
        
        print(f"❌ Agent 失败: {agent_id}")
        
        # 决策：重启或替换
        emit(EventType.REACTOR_TRIGGERED, {
            "reason": "agent_failed",
            "action": "restart_or_replace",
            "agent_id": agent_id
        })
    
    def start(self):
        """启动调度器"""
        self._check_caller_permission()
        
        self.running = True
        print("🚀 AIOS Scheduler 启动")
        
        # 主循环
        while self.running:
            try:
                # 1. 监控系统状态
                self._monitor()
                
                # 2. 判断是否需要干预
                decisions = self._decide()
                
                # 3. 触发修复动作
                for decision in decisions:
                    self._trigger(decision)
                
                # 4. 验证修复效果
                self._verify()
                
                # 5. 更新评分
                self._update_score()
                
                # 等待下一个周期
                time.sleep(10)
            
            except KeyboardInterrupt:
                print("\n⏹️ 调度器停止")
                break
            except Exception as e:
                print(f"❌ 调度器错误: {e}")
                time.sleep(5)
    
    def _monitor(self):
        """监控系统状态"""
        # 检查资源使用率
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            
            # 发射资源事件
            if cpu > 80:
                emit(EventType.RESOURCE_SPIKE, {
                    "resource": "cpu",
                    "value": cpu,
                    "threshold": 80
                })
            
            if memory > 75:
                emit(EventType.RESOURCE_SPIKE, {
                    "resource": "memory",
                    "value": memory,
                    "threshold": 75
                })
        except:
            pass
    
    def _decide(self) -> List[Dict]:
        """判断是否需要干预"""
        decisions = []
        
        # 基于最近事件做决策
        recent_events = self.event_bus.get_recent_events(limit=10)
        
        # 统计错误事件
        error_count = sum(1 for e in recent_events if 'failed' in e['type'] or 'error' in e['type'])
        
        if error_count > 3:
            decisions.append({
                "reason": "high_error_rate",
                "action": "reduce_load",
                "priority": "high"
            })
        
        return decisions
    
    def _trigger(self, decision: Dict):
        """触发修复动作"""
        self._check_caller_permission()
        
        action = decision.get('action')
        
        print(f"⚡ 触发动作: {action}")
        
        emit(EventType.REACTOR_TRIGGERED, decision)
    
    def _verify(self):
        """验证修复效果"""
        # 检查最近的 Reactor 执行结果
        pass
    
    def _update_score(self):
        """更新系统评分"""
        # 计算新的 Evolution Score
        pass
    
    def stop(self):
        """停止调度器"""
        self.running = False

if __name__ == '__main__':
    # 启动调度器
    scheduler = Scheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        scheduler.stop()
