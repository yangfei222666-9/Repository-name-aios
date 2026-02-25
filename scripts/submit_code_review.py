import sys
from pathlib import Path
sys.path.insert(0, 'aios/agent_system')
from auto_dispatcher import AutoDispatcher

workspace = Path('aios/agent_system/data')
dispatcher = AutoDispatcher(workspace)

# 提交代码审查任务
task = {
    'task': '代码审查：aios/core/reactor.py - 检查性能、安全性、可维护性',
    'task_type': 'code',
    'context': {
        'file': 'aios/core/reactor.py',
        'focus': ['performance', 'security', 'maintainability']
    }
}

print('提交任务到队列...')
result = dispatcher.submit_task(**task)
task_id = result.get('task_id', '?')
status = result.get('status', '?')
print(f'任务 ID: {task_id}')
print(f'状态: {status}')
print()
print('任务已入队，等待 Agent 处理')
print('查看队列: python aios/agent_system/auto_dispatcher.py status')
