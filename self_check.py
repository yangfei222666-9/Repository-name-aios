"""AIOS 自我检查脚本"""
from pathlib import Path
from datetime import datetime
import json
import sys

workspace = Path(r"C:\Users\A\.openclaw\workspace")

print("=" * 60)
print("AIOS 自我检查")
print("=" * 60)
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

issues = []
warnings = []
ok_count = 0

# 1. 核心组件检查
print("🔍 核心组件检查")
print("-" * 60)

# EventBus
events_dir = workspace / "aios" / "data" / "events"
if events_dir.exists():
    files = list(events_dir.glob("*.jsonl"))
    total_size = sum(f.stat().st_size for f in files)
    print(f"✅ EventBus: {len(files)} 个事件文件, {total_size} bytes")
    ok_count += 1
else:
    print("❌ EventBus: 事件目录不存在")
    issues.append("EventBus 事件目录缺失")

# Agent System
agent_data = workspace / "aios" / "agent_system" / "data"
if agent_data.exists():
    agents_file = agent_data / "agents.jsonl"
    if agents_file.exists():
        agents = []
        with open(agents_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    agents.append(json.loads(line))
        
        active = [a for a in agents if a.get('status') == 'active']
        archived = [a for a in agents if a.get('status') == 'archived']
        
        print(f"✅ Agent System: {len(agents)} 个 Agent ({len(active)} 活跃, {len(archived)} 已归档)")
        ok_count += 1
        
        if len(active) == 0:
            warnings.append("没有活跃的 Agent")
    else:
        print("⚠️  Agent System: agents.jsonl 不存在")
        warnings.append("agents.jsonl 缺失")
else:
    print("❌ Agent System: 数据目录不存在")
    issues.append("Agent System 数据目录缺失")

# Reactor
playbooks_file = workspace / "aios" / "data" / "playbooks.json"
playbooks_dir = workspace / "aios" / "playbooks"
if playbooks_file.exists():
    with open(playbooks_file, 'r', encoding='utf-8') as f:
        pb_data = json.load(f)
        pb_count = len(pb_data) if isinstance(pb_data, list) else len(pb_data.get('playbooks', []))
    print(f"✅ Reactor: {pb_count} 个 Playbook (playbooks.json)")
    ok_count += 1
elif playbooks_dir.exists():
    playbooks = list(playbooks_dir.glob("*.json")) + list(playbooks_dir.glob("*.yaml"))
    print(f"✅ Reactor: {len(playbooks)} 个 Playbook (playbooks/)")
    ok_count += 1
else:
    print("❌ Reactor: Playbook 文件不存在")
    issues.append("Reactor Playbook 缺失")

# ScoreEngine
score_file = workspace / "aios" / "learning" / "metrics_history.jsonl"
if score_file.exists():
    size = score_file.stat().st_size
    print(f"✅ ScoreEngine: 指标历史 {size} bytes")
    ok_count += 1
else:
    print("⚠️  ScoreEngine: 指标历史文件不存在")
    warnings.append("ScoreEngine 指标历史缺失")

print()

# 2. 配置文件检查
print("⚙️  配置文件检查")
print("-" * 60)

# Agent 配置
agent_config = agent_data / "agent_configs.json"
if agent_config.exists():
    with open(agent_config, 'r', encoding='utf-8') as f:
        config = json.load(f)
        agents_cfg = config.get('agents', {})
        
        # 检查是否有角色信息
        has_role = sum(1 for a in agents_cfg.values() if 'role' in a)
        
        print(f"✅ Agent 配置: {len(agents_cfg)} 个配置, {has_role} 个有角色信息")
        ok_count += 1
        
        if has_role < len(agents_cfg):
            warnings.append(f"{len(agents_cfg) - has_role} 个 Agent 缺少角色信息")
else:
    print("❌ Agent 配置: agent_configs.json 不存在")
    issues.append("Agent 配置文件缺失")

# Self-Improving Loop 状态
loop_state = agent_data / "loop_state.json"
if loop_state.exists():
    with open(loop_state, 'r', encoding='utf-8') as f:
        state = json.load(f)
        last_improvement = state.get('last_improvement', {})
        print(f"✅ Self-Improving Loop: {len(last_improvement)} 个 Agent 有改进记录")
        ok_count += 1
else:
    print("⚠️  Self-Improving Loop: 状态文件不存在")
    warnings.append("Self-Improving Loop 状态缺失")

print()

# 3. 任务队列检查
print("📋 任务队列检查")
print("-" * 60)

queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
if queue_file.exists():
    tasks = []
    with open(queue_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    if tasks:
        high = sum(1 for t in tasks if t.get('priority') == 'high')
        normal = sum(1 for t in tasks if t.get('priority') == 'normal')
        low = sum(1 for t in tasks if t.get('priority') == 'low')
        
        print(f"⚠️  任务队列: {len(tasks)} 个待处理任务")
        print(f"   优先级分布: high={high}, normal={normal}, low={low}")
        
        if len(tasks) > 10:
            warnings.append(f"任务队列积压 ({len(tasks)} 个任务)")
        else:
            warnings.append(f"有 {len(tasks)} 个待处理任务")
    else:
        print("✅ 任务队列: 空")
        ok_count += 1
else:
    print("✅ 任务队列: 不存在（空）")
    ok_count += 1

# Spawn 请求
spawn_file = workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
if spawn_file.exists():
    requests = []
    with open(spawn_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))
    
    if requests:
        print(f"⚠️  Spawn 请求: {len(requests)} 个待处理")
        warnings.append(f"有 {len(requests)} 个待处理 Spawn 请求")
    else:
        print("✅ Spawn 请求: 空")
        ok_count += 1
else:
    print("✅ Spawn 请求: 不存在（空）")
    ok_count += 1

print()

# 4. 文档检查
print("📚 文档检查")
print("-" * 60)

docs = [
    ("README.md", workspace / "aios" / "README.md"),
    ("INSTALL.md", workspace / "aios" / "INSTALL.md"),
    ("CHECKLIST.md", workspace / "aios" / "CHECKLIST.md"),
]

for name, path in docs:
    if path.exists():
        size = path.stat().st_size
        print(f"✅ {name}: {size} bytes")
        ok_count += 1
    else:
        print(f"❌ {name}: 不存在")
        issues.append(f"{name} 缺失")

print()

# 5. 总结
print("=" * 60)
print("检查总结")
print("=" * 60)

total_checks = ok_count + len(warnings) + len(issues)
print(f"总计检查项: {total_checks}")
print(f"✅ 正常: {ok_count}")
print(f"⚠️  警告: {len(warnings)}")
print(f"❌ 错误: {len(issues)}")
print()

if issues:
    print("❌ 发现的问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    print()

if warnings:
    print("⚠️  警告信息:")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")
    print()

# 健康评分
health_score = (ok_count / total_checks) * 100 if total_checks > 0 else 0
print(f"健康评分: {health_score:.1f}/100")

if health_score >= 90:
    print("状态: 🟢 优秀")
elif health_score >= 70:
    print("状态: 🟡 良好")
elif health_score >= 50:
    print("状态: 🟠 一般")
else:
    print("状态: 🔴 需要关注")

print()
print("=" * 60)

# 返回状态码
if issues:
    sys.exit(1)
elif warnings:
    sys.exit(0)
else:
    sys.exit(0)
