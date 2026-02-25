#!/usr/bin/env python3
"""测试覆盖率检查 - 扫描 aios/ 目录，找出缺少测试的模块"""

import os
from pathlib import Path
from collections import defaultdict

def scan_modules(base_path: Path):
    """扫描所有 Python 模块"""
    modules = []
    for root, dirs, files in os.walk(base_path):
        # 跳过测试目录、__pycache__、.git 等
        dirs[:] = [d for d in dirs if d not in ['tests', '__pycache__', '.git', 'node_modules', '.venv']]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('test_'):
                rel_path = Path(root) / file
                modules.append(rel_path.relative_to(base_path))
    
    return modules

def scan_tests(base_path: Path):
    """扫描所有测试文件"""
    tests = []
    test_dir = base_path / 'tests'
    
    if not test_dir.exists():
        return tests
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                tests.append(file)
    
    return tests

def extract_tested_modules(tests):
    """从测试文件名提取被测试的模块"""
    tested = set()
    for test_file in tests:
        # test_event_bus.py -> event_bus
        # test_reactor_retry.py -> reactor_retry
        module_name = test_file.replace('test_', '').replace('.py', '')
        tested.add(module_name)
    
    return tested

def categorize_modules(modules):
    """按类别分组模块"""
    categories = defaultdict(list)
    
    for module in modules:
        parts = module.parts
        
        if 'core' in parts:
            categories['core'].append(module)
        elif 'agent_system' in parts:
            categories['agent_system'].append(module)
        elif 'learning' in parts:
            categories['learning'].append(module)
        elif 'scripts' in parts:
            categories['scripts'].append(module)
        else:
            categories['other'].append(module)
    
    return categories

def calculate_priority(module: Path):
    """计算模块优先级（1-5，5 最高）"""
    name = module.name.lower()
    
    # 核心模块
    if any(x in name for x in ['event_bus', 'scheduler', 'reactor', 'event_store']):
        return 5
    
    # Agent 系统
    if 'agent' in name and 'agent_system' in str(module):
        return 4
    
    # 学习系统
    if 'learning' in str(module) or 'evolution' in name:
        return 4
    
    # 工具脚本
    if 'scripts' in str(module):
        return 2
    
    # 测试生成脚本
    if 'generate' in name or 'stress' in name:
        return 1
    
    return 3

if __name__ == '__main__':
    base_path = Path(__file__).parent.parent
    
    print("Scanning AIOS modules...\n")
    
    # 扫描模块和测试
    modules = scan_modules(base_path)
    tests = scan_tests(base_path)
    tested_modules = extract_tested_modules(tests)
    
    print(f"Total modules: {len(modules)}")
    print(f"Total tests: {len(tests)}")
    print(f"Tested modules: {len(tested_modules)}\n")
    
    # 找出未覆盖的模块
    uncovered = []
    for module in modules:
        module_name = module.stem  # 文件名（不含扩展名）
        
        # 检查是否有对应的测试
        is_tested = any(module_name in tested for tested in tested_modules)
        
        if not is_tested:
            priority = calculate_priority(module)
            uncovered.append((module, priority))
    
    # 按优先级排序
    uncovered.sort(key=lambda x: x[1], reverse=True)
    
    print(f"Uncovered modules: {len(uncovered)}\n")
    
    # 按类别分组
    categories = categorize_modules([m for m, _ in uncovered])
    
    print("=" * 80)
    print("UNCOVERED MODULES BY CATEGORY")
    print("=" * 80)
    
    for category, mods in sorted(categories.items()):
        print(f"\n[{category.upper()}] ({len(mods)} modules)")
        
        # 按优先级排序
        mods_with_priority = [(m, calculate_priority(m)) for m in mods]
        mods_with_priority.sort(key=lambda x: x[1], reverse=True)
        
        for module, priority in mods_with_priority:
            priority_str = "P" + str(priority)
            print(f"  [{priority_str}] {module}")
    
    print("\n" + "=" * 80)
    print("PRIORITY LEGEND")
    print("=" * 80)
    print("[P5] - Critical (core modules)")
    print("[P4] - High (agent/learning systems)")
    print("[P3] - Medium (utilities)")
    print("[P2] - Low (scripts)")
    print("[P1] - Very Low (test generators)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    # 统计各优先级数量
    priority_counts = defaultdict(int)
    for _, priority in uncovered:
        priority_counts[priority] += 1
    
    print(f"\nCritical (P5): {priority_counts[5]} modules - Test immediately")
    print(f"High (P4): {priority_counts[4]} modules - Test this week")
    print(f"Medium (P3): {priority_counts[3]} modules - Test this month")
    print(f"Low (P2): {priority_counts[2]} modules - Optional")
    print(f"Very Low (P1): {priority_counts[1]} modules - Skip")
    
    # 计算覆盖率
    coverage = (len(tested_modules) / len(modules) * 100) if modules else 0
    print(f"\nCurrent test coverage: {coverage:.1f}%")
    
    # 如果加上 P5 模块
    p5_count = priority_counts[5]
    target_coverage = ((len(tested_modules) + p5_count) / len(modules) * 100) if modules else 0
    print(f"Target coverage (with P5): {target_coverage:.1f}%")
