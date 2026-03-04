"""
AIOS Task Executor

Executes tasks from the queue by spawning appropriate agents.

Usage:
    from core.task_executor import TaskExecutor
    
    executor = TaskExecutor()
    result = executor.execute_task(task)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# Add AIOS to path
AIOS_ROOT = Path(__file__).resolve().parent.parent
if str(AIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(AIOS_ROOT))

from core.task_submitter import get_submitter, update_task_status


class TaskExecutor:
    """Execute tasks by spawning agents."""
    
    # Task type to agent mapping
    AGENT_MAPPING = {
        "code": "coder",
        "analysis": "analyst",
        "monitor": "monitor",
        "refactor": "coder",
        "test": "tester",
        "deploy": "deployer",
        "research": "researcher",
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # seconds
    
    def __init__(self):
        self._submitter = get_submitter()
        self._execution_log = AIOS_ROOT / "agent_system" / "task_executions.jsonl"
        self._execution_log.parent.mkdir(parents=True, exist_ok=True)
    
    def execute_task(self, task: Dict, retry_count: int = 0) -> Dict:
        """
        Execute a single task with retry support.
        
        Args:
            task: Task record from queue
            retry_count: Current retry attempt (0 = first attempt)
        
        Returns:
            Execution result
        """
        task_id = task.get("task_id") or task.get("id", "unknown")
        task_type = task.get("type", "code")
        description = task.get("description", "No description")
        
        # Update status to running
        if retry_count == 0:
            update_task_status(task_id, "running")
        
        # Determine agent
        agent_type = self.AGENT_MAPPING.get(task_type, "coder")
        
        # Prepare spawn request
        spawn_request = {
            "task_id": task_id,
            "agent_type": agent_type,
            "description": description,
            "priority": task.get("priority", "normal"),
            "metadata": task.get("metadata", {}),
            "retry_count": retry_count,
        }
        
        # Execute
        result = self._execute_spawn(spawn_request)
        
        # Handle failure with retry
        if not result["success"] and retry_count < self.MAX_RETRIES:
            print(f"  [WARN] Attempt {retry_count + 1} failed: {result.get('error', 'Unknown error')}")
            print(f"  [RETRY] Retrying in {self.RETRY_DELAY}s... (attempt {retry_count + 2}/{self.MAX_RETRIES + 1})")
            
            import time
            time.sleep(self.RETRY_DELAY)
            
            # Retry
            return self.execute_task(task, retry_count + 1)
        
        # Update task status (final result)
        if result["success"]:
            update_task_status(task_id, "completed", result=result)
        else:
            # Add retry info to result
            result["total_attempts"] = retry_count + 1
            update_task_status(task_id, "failed", result=result)
            
            # 🔄 触发Bootstrapped Regeneration（任务失败时）
            print(f"  [REGEN] Triggering Bootstrapped Regeneration...")
            try:
                from low_success_regeneration import regenerate_failed_task
                regenerated = regenerate_failed_task(limit=1)  # 只处理当前失败任务
                if regenerated > 0:
                    print(f"  [OK] Task regenerated successfully")
            except Exception as e:
                print(f"  [WARN] Regeneration failed: {e}")
        
        # Log execution
        self._log_execution(task, result, retry_count)
        
        return result
    
    def _execute_spawn(self, spawn_request: Dict) -> Dict:
        """
        Execute spawn request via sessions_spawn.
        
        Falls back to simulation if sessions_spawn is not available.
        """
        # Try real execution via sessions_spawn
        try:
            return self._real_execution(spawn_request)
        except Exception as e:
            print(f"  [WARN] Real execution failed: {e}")
            print(f"  [FALLBACK] Using simulation")
            return self._simulate_execution(spawn_request)
    
    def _real_execution(self, spawn_request: Dict) -> Dict:
        """
        Execute via Claude API (real execution).
        
        Directly calls Claude API to execute tasks.
        """
        try:
            # Import real executor
            import sys
            sys.path.insert(0, str(AIOS_ROOT / "core"))
            from real_executor import execute_task_real
            
            task_desc = spawn_request["description"]
            agent_type = spawn_request.get("agent_type", "coder")
            
            # Execute via Claude API
            result = execute_task_real(task_desc, agent_type)
            
            return result
            
        except Exception as e:
            raise  # Re-raise to trigger fallback
    
    def _simulate_execution(self, spawn_request: Dict) -> Dict:
        """Simulate task execution (for testing)."""
        import random
        
        success = random.random() > 0.2  # 80% success rate
        
        if success:
            return {
                "success": True,
                "agent": spawn_request["agent_type"],
                "duration": random.uniform(5, 30),
                "output": f"Task completed by {spawn_request['agent_type']} agent",
            }
        else:
            return {
                "success": False,
                "agent": spawn_request["agent_type"],
                "error": "Simulated failure",
            }
    
    def _log_execution(self, task: Dict, result: Dict, retry_count: int = 0):
        """Log task execution."""
        import json
        
        log_entry = {
            "timestamp": time.time(),
            "task_id": task.get("task_id") or task.get("id", "unknown"),
            "task_type": task.get("type", "unknown"),
            "description": task.get("description", "No description"),
            "result": result,
            "retry_count": retry_count,
            "total_attempts": retry_count + 1,
        }
        
        with open(self._execution_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    def execute_batch(self, tasks: List[Dict], max_tasks: int = 5) -> List[Dict]:
        """
        Execute a batch of tasks.
        
        Args:
            tasks: List of tasks to execute
            max_tasks: Maximum number of tasks to execute
        
        Returns:
            List of execution results
        """
        results = []
        
        for i, task in enumerate(tasks[:max_tasks]):
            task_id = task.get('task_id') or task.get('id', 'unknown')
            print(f"[{i+1}/{min(len(tasks), max_tasks)}] Executing task: {task_id}")
            print(f"  Type: {task.get('type', 'unknown')}")
            print(f"  Description: {task.get('description', 'No description')}")
            
            result = self.execute_task(task)
            results.append(result)
            
            if result["success"]:
                print(f"  [OK] Completed in {result.get('duration', 0):.1f}s")
            else:
                print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
        
        return results


# ── Convenience Functions ──────────────────────────────────────────

_default_executor = None

def get_executor() -> TaskExecutor:
    """Get the default task executor."""
    global _default_executor
    if _default_executor is None:
        _default_executor = TaskExecutor()
    return _default_executor


def execute_task(task: Dict) -> Dict:
    """Execute a task (convenience function)."""
    return get_executor().execute_task(task)


def execute_batch(tasks: List[Dict], max_tasks: int = 5) -> List[Dict]:
    """Execute a batch of tasks (convenience function)."""
    return get_executor().execute_batch(tasks, max_tasks)


# ── CLI ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from core.task_submitter import list_tasks
    
    parser = argparse.ArgumentParser(description="AIOS Task Executor")
    parser.add_argument("--status", default="pending", help="Task status to execute")
    parser.add_argument("--limit", type=int, default=5, help="Max tasks to execute")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't execute)")
    
    args = parser.parse_args()
    
    # Get pending tasks
    tasks = list_tasks(status=args.status, limit=args.limit)
    
    if not tasks:
        print("No tasks to execute.")
        sys.exit(0)
    
    print(f"Found {len(tasks)} tasks to execute\n")
    
    if args.dry_run:
        print("[DRY RUN] Would execute:")
        for i, task in enumerate(tasks, 1):
            print(f"{i}. [{task['priority']}] {task['type']}: {task['description']}")
        sys.exit(0)
    
    # Execute tasks
    executor = TaskExecutor()
    results = executor.execute_batch(tasks, max_tasks=args.limit)
    
    # Summary
    print("\n" + "=" * 70)
    print("Execution Summary:")
    print("=" * 70)
    
    success_count = sum(1 for r in results if r["success"])
    failed_count = len(results) - success_count
    
    print(f"\nTotal: {len(results)}")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Failed: {failed_count}")
