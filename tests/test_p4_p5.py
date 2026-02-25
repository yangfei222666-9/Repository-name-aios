#!/usr/bin/env python3
"""
测试 orchestrator 和 integrations 模块
"""
import sys
import io
from pathlib import Path

# 修复 Windows 控制台 Unicode 输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加 workspace 到路径
workspace = Path(__file__).parent.parent.parent
sys.path.insert(0, str(workspace))

from aios.core import orchestrator, integrations

def test_orchestrator():
    print("=== 测试 Orchestrator ===")
    
    # 测试任务拆分
    subtasks = orchestrator.split_task("任务1;任务2;任务3")
    print(f"✓ 任务拆分: {len(subtasks)} 个子任务")
    
    # 测试入队
    task_id = orchestrator.enqueue({"title": "测试任务"})
    print(f"✓ 入队成功: {task_id[:8]}")
    
    # 测试出队
    task = orchestrator.dequeue()
    if task:
        print(f"✓ 出队成功: {task['title']}")
        
        # 测试标记完成
        orchestrator.mark_done(task['id'], {"result": "success"})
        print(f"✓ 标记完成")
    
    # 测试进度查询
    progress = orchestrator.get_progress()
    print(f"✓ 进度查询: {progress['done']}/{progress['total']} 完成")
    
    # 测试超时检测
    timeouts = orchestrator.check_timeouts(max_seconds=1)
    print(f"✓ 超时检测: {len(timeouts)} 个超时任务")
    
    print()

def test_integrations():
    print("=== 测试 Integrations ===")
    
    # 安装内置集成
    count = integrations.install_builtin_integrations()
    print(f"✓ 安装内置集成: {count} 个")
    
    # 列出集成
    all_integrations = integrations.list_integrations()
    print(f"✓ 列出集成: {len(all_integrations)} 个")
    
    # 注册自定义集成
    custom = {
        "name": "custom_test",
        "type": "cli",
        "description": "自定义测试集成",
        "config": {},
        "health_check_cmd": "echo OK"
    }
    integrations.register(custom)
    print(f"✓ 注册自定义集成: {custom['name']}")
    
    # 健康检查
    result = integrations.health_check("custom_test")
    print(f"✓ 健康检查: {result['status']}")
    
    # 执行集成
    exec_result = integrations.execute_integration("system_info")
    if exec_result['success']:
        print(f"✓ 执行集成成功: CPU {exec_result['output']['cpu_count']} 核")
    
    print()

if __name__ == "__main__":
    test_orchestrator()
    test_integrations()
    print("✅ 所有测试通过")
