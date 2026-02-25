#!/usr/bin/env python3
"""
AIOS Workflow Manager
工作流管理：导入、导出、执行、调度
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

AIOS_ROOT = Path(__file__).parent
WORKFLOWS_FILE = AIOS_ROOT / "workflows.json"

def load_workflows() -> List[Dict]:
    """加载工作流"""
    if not WORKFLOWS_FILE.exists():
        return []
    
    with open(WORKFLOWS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get('workflows', [])

def save_workflows(workflows: List[Dict]):
    """保存工作流"""
    with open(WORKFLOWS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'workflows': workflows}, f, indent=2, ensure_ascii=False)

def list_workflows():
    """列出所有工作流"""
    workflows = load_workflows()
    
    print(f"📋 共有 {len(workflows)} 个工作流\n")
    
    for wf in workflows:
        status = "✅ 启用" if wf.get('enabled', True) else "❌ 禁用"
        print(f"{status} [{wf['id']}] {wf['name']}")
        print(f"   描述: {wf['description']}")
        
        schedule = wf.get('schedule', {})
        if schedule.get('type') == 'cron':
            print(f"   调度: Cron {schedule.get('cron')}")
        elif schedule.get('type') == 'interval':
            print(f"   调度: 每 {schedule.get('interval_minutes')} 分钟")
        
        print(f"   步骤: {len(wf.get('steps', []))} 个")
        print()

def execute_workflow(workflow_id: str):
    """执行工作流"""
    workflows = load_workflows()
    workflow = next((wf for wf in workflows if wf['id'] == workflow_id), None)
    
    if not workflow:
        print(f"❌ 工作流 {workflow_id} 不存在")
        return
    
    if not workflow.get('enabled', True):
        print(f"⏸️ 工作流 {workflow['name']} 已禁用")
        return
    
    print(f"🚀 执行工作流: {workflow['name']}")
    print(f"📝 描述: {workflow['description']}\n")
    
    steps = workflow.get('steps', [])
    success_count = 0
    
    for i, step in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {step['name']}")
        
        step_type = step.get('type', 'command')
        
        if step_type == 'command':
            # 执行命令
            command = step.get('command', '')
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    encoding='utf-8',
                    errors='replace'
                )
                
                if result.returncode == 0:
                    print(f"   ✅ 成功")
                    success_count += 1
                else:
                    print(f"   ❌ 失败: {result.stderr[:100]}")
            except Exception as e:
                print(f"   ❌ 异常: {str(e)[:100]}")
        
        elif step_type == 'check':
            # 条件检查（简化版，实际需要实现条件解析）
            print(f"   ⏭️ 跳过检查步骤（需要实现条件解析）")
        
        elif step_type == 'notify':
            # 通知
            message = step.get('message', '')
            print(f"   📢 通知: {message}")
            success_count += 1
        
        print()
    
    print(f"✅ 工作流执行完成: {success_count}/{len(steps)} 步骤成功")

def import_workflow(file_path: str):
    """导入工作流"""
    import_file = Path(file_path)
    
    if not import_file.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    with open(import_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    new_workflows = data.get('workflows', [])
    
    if not new_workflows:
        print("❌ 没有找到工作流")
        return
    
    existing_workflows = load_workflows()
    existing_ids = {wf['id'] for wf in existing_workflows}
    
    imported = 0
    skipped = 0
    
    for wf in new_workflows:
        if wf['id'] in existing_ids:
            print(f"⏭️ 跳过已存在的工作流: {wf['name']}")
            skipped += 1
        else:
            existing_workflows.append(wf)
            print(f"✅ 导入工作流: {wf['name']}")
            imported += 1
    
    if imported > 0:
        save_workflows(existing_workflows)
    
    print(f"\n📊 导入完成: {imported} 个新工作流，{skipped} 个跳过")

def export_workflow(workflow_id: str, output_file: str):
    """导出工作流"""
    workflows = load_workflows()
    workflow = next((wf for wf in workflows if wf['id'] == workflow_id), None)
    
    if not workflow:
        print(f"❌ 工作流 {workflow_id} 不存在")
        return
    
    output_path = Path(output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({'workflows': [workflow]}, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 工作流已导出到: {output_file}")

def enable_workflow(workflow_id: str):
    """启用工作流"""
    workflows = load_workflows()
    workflow = next((wf for wf in workflows if wf['id'] == workflow_id), None)
    
    if not workflow:
        print(f"❌ 工作流 {workflow_id} 不存在")
        return
    
    workflow['enabled'] = True
    save_workflows(workflows)
    print(f"✅ 已启用工作流: {workflow['name']}")

def disable_workflow(workflow_id: str):
    """禁用工作流"""
    workflows = load_workflows()
    workflow = next((wf for wf in workflows if wf['id'] == workflow_id), None)
    
    if not workflow:
        print(f"❌ 工作流 {workflow_id} 不存在")
        return
    
    workflow['enabled'] = False
    save_workflows(workflows)
    print(f"⏸️ 已禁用工作流: {workflow['name']}")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python workflow_manager.py list                    # 列出所有工作流")
        print("  python workflow_manager.py execute <workflow_id>   # 执行工作流")
        print("  python workflow_manager.py import <file>           # 导入工作流")
        print("  python workflow_manager.py export <id> <file>      # 导出工作流")
        print("  python workflow_manager.py enable <workflow_id>    # 启用工作流")
        print("  python workflow_manager.py disable <workflow_id>   # 禁用工作流")
        return
    
    command = sys.argv[1]
    
    if command == 'list':
        list_workflows()
    elif command == 'execute' and len(sys.argv) >= 3:
        execute_workflow(sys.argv[2])
    elif command == 'import' and len(sys.argv) >= 3:
        import_workflow(sys.argv[2])
    elif command == 'export' and len(sys.argv) >= 4:
        export_workflow(sys.argv[2], sys.argv[3])
    elif command == 'enable' and len(sys.argv) >= 3:
        enable_workflow(sys.argv[2])
    elif command == 'disable' and len(sys.argv) >= 3:
        disable_workflow(sys.argv[2])
    else:
        print("❌ 未知命令或参数不足")

if __name__ == '__main__':
    main()
