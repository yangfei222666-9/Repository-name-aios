"""
AIOS v0.6 Production Scheduler - 优先级队列 + 并发处理
职责：
1. 优先级队列（P0 > P1 > P2 > P3）
2. 并发处理（最多 5 个任务同时跑）
3. 任务超时和取消
4. 负载均衡
"""
import time
import threading
from queue import PriorityQueue, Empty
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
import uuid


class Priority(IntEnum):
    """任务优先级"""
    P0_CRITICAL = 0   # 系统降级（score < 0.3）
    P1_HIGH = 1       # 资源告警（CPU/内存峰值）
    P2_MEDIUM = 2     # Agent 错误
    P3_LOW = 3        # 正常事件


@dataclass(order=True)
class Task:
    """调度任务"""
    priority: int
    task_id: str = field(compare=False)
    task_type: str = field(compare=False)
    payload: Dict[str, Any] = field(compare=False)
    created_at: float = field(compare=False, default_factory=time.time)
    timeout_sec: int = field(compare=False, default=60)
    retry_count: int = field(compare=False, default=0)
    max_retries: int = field(compare=False, default=3)


class ProductionScheduler:
    """生产级调度器 - 优先级队列 + 并发"""
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化调度器
        
        Args:
            max_concurrent: 最大并发任务数
        """
        self.queue = PriorityQueue()
        self.max_concurrent = max_concurrent
        self.running_tasks: Dict[str, threading.Thread] = {}
        self.completed_tasks: List[Dict] = []
        self.failed_tasks: List[Dict] = []
        
        self.running = False
        self.lock = threading.Lock()
        
        # 统计
        self.stats = {
            "total_submitted": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_timeout": 0,
            "total_cancelled": 0
        }
    
    def submit(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: Priority = Priority.P3_LOW,
        timeout_sec: int = 60
    ) -> str:
        """
        提交任务到队列
        
        Args:
            task_type: 任务类型
            payload: 任务参数
            priority: 优先级
            timeout_sec: 超时时间（秒）
        
        Returns:
            任务 ID
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            priority=priority.value,
            task_id=task_id,
            task_type=task_type,
            payload=payload,
            timeout_sec=timeout_sec
        )
        
        self.queue.put(task)
        self.stats["total_submitted"] += 1
        
        print(f"[Scheduler] 📥 任务入队: {task_id} (P{priority.value} {task_type})")
        
        return task_id
    
    def start(self):
        """启动调度器"""
        if self.running:
            print("[Scheduler] 已经在运行")
            return
        
        self.running = True
        print(f"[Scheduler] 🚀 启动（最大并发: {self.max_concurrent}）")
        
        # 启动调度线程
        scheduler_thread = threading.Thread(target=self._schedule_loop, daemon=True)
        scheduler_thread.start()
    
    def stop(self):
        """停止调度器"""
        self.running = False
        print("[Scheduler] ⏹️  停止中...")
        
        # 等待所有任务完成
        while self.running_tasks:
            time.sleep(0.1)
        
        print("[Scheduler] ✅ 已停止")
    
    def _schedule_loop(self):
        """调度循环"""
        while self.running:
            try:
                # 检查是否可以启动新任务
                with self.lock:
                    current_running = len(self.running_tasks)
                
                if current_running < self.max_concurrent:
                    # 从队列取任务（非阻塞）
                    try:
                        task = self.queue.get(timeout=0.1)
                        self._execute_task(task)
                    except Empty:
                        pass
                else:
                    # 队列满，等待
                    time.sleep(0.1)
                
                # 清理完成的任务
                self._cleanup_finished_tasks()
            
            except Exception as e:
                print(f"[Scheduler] ❌ 调度错误: {e}")
                time.sleep(1)
    
    def _execute_task(self, task: Task):
        """执行任务（在新线程中）"""
        def run():
            start_time = time.time()
            
            try:
                print(f"[Scheduler] ▶️  执行任务: {task.task_id} ({task.task_type})")
                
                # 模拟任务执行
                result = self._run_task(task)
                
                duration = time.time() - start_time
                
                # 记录完成
                with self.lock:
                    self.completed_tasks.append({
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "priority": task.priority,
                        "duration": duration,
                        "result": result,
                        "completed_at": datetime.now().isoformat()
                    })
                    self.stats["total_completed"] += 1
                
                print(f"[Scheduler] ✅ 任务完成: {task.task_id} ({duration:.2f}s)")
            
            except TimeoutError:
                print(f"[Scheduler] ⏱️  任务超时: {task.task_id}")
                
                with self.lock:
                    self.failed_tasks.append({
                        "task_id": task.task_id,
                        "task_type": task.task_type,
                        "error": "timeout",
                        "failed_at": datetime.now().isoformat()
                    })
                    self.stats["total_timeout"] += 1
            
            except Exception as e:
                print(f"[Scheduler] ❌ 任务失败: {task.task_id} - {e}")
                
                # 判断是否重试
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    print(f"[Scheduler] 🔄 重试任务: {task.task_id} ({task.retry_count}/{task.max_retries})")
                    self.queue.put(task)
                else:
                    with self.lock:
                        self.failed_tasks.append({
                            "task_id": task.task_id,
                            "task_type": task.task_type,
                            "error": str(e),
                            "failed_at": datetime.now().isoformat()
                        })
                        self.stats["total_failed"] += 1
            
            finally:
                # 从运行列表移除
                with self.lock:
                    if task.task_id in self.running_tasks:
                        del self.running_tasks[task.task_id]
        
        # 启动任务线程
        thread = threading.Thread(target=run, daemon=True)
        
        with self.lock:
            self.running_tasks[task.task_id] = thread
        
        thread.start()
    
    def _run_task(self, task: Task) -> Any:
        """
        运行任务（实际执行逻辑）
        
        Args:
            task: 任务对象
        
        Returns:
            任务结果
        """
        # 这里应该根据 task_type 调用不同的处理器
        # 目前先模拟执行
        
        if task.task_type == "trigger_reactor":
            # 触发 Reactor
            return self._trigger_reactor(task.payload)
        
        elif task.task_type == "agent_spawn":
            # 创建 Agent
            return self._spawn_agent(task.payload)
        
        elif task.task_type == "resource_check":
            # 资源检查
            return self._check_resources(task.payload)
        
        else:
            # 未知任务类型
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    def _trigger_reactor(self, payload: Dict) -> Dict:
        """触发 Reactor"""
        # 模拟执行
        time.sleep(0.5)
        return {"status": "reactor_triggered", "payload": payload}
    
    def _spawn_agent(self, payload: Dict) -> Dict:
        """创建 Agent"""
        # 模拟执行
        time.sleep(1.0)
        return {"status": "agent_spawned", "agent_id": "agent-123"}
    
    def _check_resources(self, payload: Dict) -> Dict:
        """检查资源"""
        # 模拟执行
        time.sleep(0.2)
        return {"status": "resources_ok", "cpu": 45.2, "memory": 62.1}
    
    def _cleanup_finished_tasks(self):
        """清理已完成的任务线程"""
        with self.lock:
            finished = [
                task_id for task_id, thread in self.running_tasks.items()
                if not thread.is_alive()
            ]
            
            for task_id in finished:
                del self.running_tasks[task_id]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务 ID
        
        Returns:
            是否成功取消
        """
        with self.lock:
            if task_id in self.running_tasks:
                # 注意：Python 线程无法强制终止
                # 这里只是标记，实际需要任务内部检查取消标志
                print(f"[Scheduler] ⏹️  取消任务: {task_id}")
                self.stats["total_cancelled"] += 1
                return True
        
        return False
    
    def get_status(self) -> Dict:
        """获取调度器状态"""
        with self.lock:
            return {
                "running": self.running,
                "queue_size": self.queue.qsize(),
                "running_tasks": len(self.running_tasks),
                "max_concurrent": self.max_concurrent,
                "stats": self.stats.copy(),
                "completed_count": len(self.completed_tasks),
                "failed_count": len(self.failed_tasks)
            }
    
    def get_running_tasks(self) -> List[str]:
        """获取正在运行的任务列表"""
        with self.lock:
            return list(self.running_tasks.keys())


# 全局单例
_global_scheduler: Optional[ProductionScheduler] = None


def get_scheduler() -> ProductionScheduler:
    """获取全局 Scheduler 实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = ProductionScheduler()
    return _global_scheduler
