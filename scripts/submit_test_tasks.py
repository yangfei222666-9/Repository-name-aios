"""
AIOS 真实任务 + 边界测试
阶段 1：真实任务（验证正常流程）
阶段 2：边界测试（验证自动修复）
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# 任务定义
TASKS = [
    # === 阶段 1：真实任务 ===
    {
        "task_id": "real_001",
        "label": "代码审查 - Self-Improving Loop",
        "task_type": "code",
        "priority": "normal",
        "description": "审查 aios/agent_system/self_improving_loop.py 的代码质量，检查：1) 是否有潜在 bug 2) 代码可读性 3) 性能优化空间",
        "expected_duration": 60,
    },
    {
        "task_id": "real_002", 
        "label": "性能分析 - 事件日志",
        "task_type": "analysis",
        "priority": "normal",
        "description": "分析 aios/events/events.jsonl 最近 100 条事件，找出：1) 最慢的 5 个操作 2) 高频操作 3) 优化建议",
        "expected_duration": 45,
    },
    {
        "task_id": "real_003",
        "label": "文档生成 - Agent System",
        "task_type": "code",
        "priority": "normal", 
        "description": "为 aios/agent_system/__init__.py 的 AgentSystem 类生成使用文档，包括：1) 主要功能 2) 使用示例 3) 注意事项",
        "expected_duration": 50,
    },
    
    # === 阶段 2：边界测试 ===
    {
        "task_id": "boundary_001",
        "label": "超时测试 - 短超时",
        "task_type": "code",
        "priority": "low",
        "description": "执行一个需要 30 秒的任务，但超时设置为 5 秒，验证超时处理",
        "expected_duration": 5,
        "force_timeout": True,
    },
    {
        "task_id": "boundary_002",
        "label": "失败测试 - 无效输入",
        "task_type": "code",
        "priority": "low",
        "description": "尝试读取不存在的文件 /nonexistent/file.txt，验证错误处理",
        "expected_duration": 10,
        "expect_failure": True,
    },
    {
        "task_id": "boundary_003",
        "label": "重试测试 - 网络错误",
        "task_type": "analysis",
        "priority": "low",
        "description": "模拟网络请求失败（访问 http://localhost:99999），验证重试机制",
        "expected_duration": 15,
        "expect_failure": True,
    },
]

def submit_tasks():
    """提交任务到 Agent System"""
    queue_file = Path("aios/agent_system/task_queue.jsonl")
    
    print("=" * 60)
    print("AIOS 真实任务 + 边界测试")
    print("=" * 60)
    print()
    
    # 提交任务
    submitted = []
    with open(queue_file, 'a', encoding='utf-8') as f:
        for task in TASKS:
            task_entry = {
                "task_id": task["task_id"],
                "label": task["label"],
                "task_type": task["task_type"],
                "priority": task["priority"],
                "message": task["description"],
                "submitted_at": datetime.now().isoformat(),
                "status": "pending",
                "metadata": {
                    "expected_duration": task.get("expected_duration", 60),
                    "force_timeout": task.get("force_timeout", False),
                    "expect_failure": task.get("expect_failure", False),
                }
            }
            f.write(json.dumps(task_entry, ensure_ascii=False) + '\n')
            submitted.append(task)
            
            stage = "阶段1-真实任务" if task["task_id"].startswith("real_") else "阶段2-边界测试"
            print(f"✓ [{stage}] {task['label']}")
            print(f"  类型: {task['task_type']} | 优先级: {task['priority']}")
            print(f"  描述: {task['description'][:60]}...")
            print()
    
    print(f"已提交 {len(submitted)} 个任务到队列")
    print()
    print("监控方式：")
    print("  1. Dashboard: http://127.0.0.1:9091")
    print("  2. 任务队列: aios/agent_system/task_queue.jsonl")
    print("  3. Agent 追踪: aios/agent_system/data/traces/agent_traces.jsonl")
    print()
    print("预期结果：")
    print("  - 阶段1（3个任务）：应该全部成功")
    print("  - 阶段2（3个任务）：应该触发超时/失败/重试")
    print("  - Self-Improving Loop：如果失败≥3次，应该触发改进")
    print("  - Reactor：应该自动响应失败事件")
    print()

if __name__ == "__main__":
    submit_tasks()
