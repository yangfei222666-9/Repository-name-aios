"""
直接执行测试任务 - 使用 sessions_spawn
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# 任务定义
TASKS = [
    {
        "task_id": "real_001",
        "task": "审查 aios/agent_system/self_improving_loop.py 的代码质量，检查：1) 是否有潜在 bug 2) 代码可读性 3) 性能优化空间。给出具体建议。",
        "agent_id": "coder",
    },
    {
        "task_id": "real_002",
        "task": "分析 aios/events/events.jsonl 最近 100 条事件，找出：1) 最慢的 5 个操作 2) 高频操作 3) 优化建议。",
        "agent_id": "analyst",
    },
    {
        "task_id": "real_003",
        "task": "为 aios/agent_system/__init__.py 的 AgentSystem 类生成使用文档，包括：1) 主要功能 2) 使用示例 3) 注意事项。",
        "agent_id": "coder",
    },
]

print("=" * 60)
print("执行真实任务（阶段 1）")
print("=" * 60)
print()

for task in TASKS:
    print(f"任务 {task['task_id']}: {task['task'][:60]}...")
    print(f"  派发给: {task['agent_id']}")
    print()

print("提示：这些任务将通过 sessions_spawn 在后台执行")
print("你可以通过以下方式监控：")
print("  1. subagents list - 查看运行中的 sub-agent")
print("  2. Dashboard - http://127.0.0.1:9091")
print("  3. aios/agent_system/data/traces/agent_traces.jsonl")
print()
print("要执行这些任务，请在 OpenClaw 中运行：")
print()
for task in TASKS:
    print(f"sessions_spawn(task=\"{task['task'][:80]}...\", agentId=\"{task['agent_id']}\", cleanup=\"keep\")")
print()
