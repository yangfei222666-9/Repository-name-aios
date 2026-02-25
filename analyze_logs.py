"""分析 AIOS 日志和事件"""
from pathlib import Path
from datetime import datetime
import json

workspace = Path(r"C:\Users\A\.openclaw\workspace")

print("=== AIOS 日志分析 ===\n")

# 1. 检查事件文件
events_dir = workspace / "aios" / "data" / "events"
if events_dir.exists():
    print("📊 事件文件：")
    files = sorted(events_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
    for f in files[:5]:
        size = f.stat().st_size
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {f.name}: {size} bytes, 最后修改 {mtime}")
    
    # 分析今天的事件
    today = datetime.now().strftime("%Y-%m-%d")
    today_file = events_dir / f"{today}.jsonl"
    if today_file.exists():
        print(f"\n📅 今天的事件 ({today})：")
        events = []
        with open(today_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        
        print(f"  总计: {len(events)} 个事件")
        
        # 按类型统计
        types = {}
        for e in events:
            t = e.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        
        print("\n  事件类型分布：")
        for t, c in sorted(types.items(), key=lambda x: -x[1])[:10]:
            print(f"    {t}: {c}")
        
        # 最近的事件
        print("\n  最近 5 个事件：")
        for e in events[-5:]:
            ts = datetime.fromtimestamp(e['timestamp'] / 1000).strftime("%H:%M:%S")
            print(f"    [{ts}] {e['type']} - {e.get('source', 'unknown')}")

print()

# 2. 检查 Agent 数据
agent_data = workspace / "aios" / "agent_system" / "data"
if agent_data.exists():
    print("🤖 Agent 系统：")
    
    # agents.jsonl
    agents_file = agent_data / "agents.jsonl"
    if agents_file.exists():
        agents = []
        with open(agents_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    agents.append(json.loads(line))
        
        active = [a for a in agents if a.get('status') == 'active']
        archived = [a for a in agents if a.get('status') == 'archived']
        
        print(f"  总计: {len(agents)} 个 Agent")
        print(f"  活跃: {len(active)}")
        print(f"  已归档: {len(archived)}")
    
    # loop.log
    loop_log = agent_data / "loop.log"
    if loop_log.exists():
        size = loop_log.stat().st_size
        print(f"\n  Self-Improving Loop 日志: {size} bytes")
        
        # 读取最后几行
        with open(loop_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if lines:
                print("\n  最近的日志：")
                for line in lines[-5:]:
                    print(f"    {line.strip()}")

print()

# 3. 检查任务队列
queue_file = workspace / "aios" / "agent_system" / "task_queue.jsonl"
if queue_file.exists():
    print("📋 任务队列：")
    tasks = []
    with open(queue_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                tasks.append(json.loads(line))
    
    if tasks:
        print(f"  待处理任务: {len(tasks)}")
        for task in tasks[:5]:
            print(f"    {task.get('id')}: {task.get('type')} - {task.get('priority', 'normal')}")
    else:
        print("  队列为空")

print()

# 4. 检查 spawn_requests
spawn_file = workspace / "aios" / "agent_system" / "spawn_requests.jsonl"
if spawn_file.exists():
    print("🚀 Spawn 请求：")
    requests = []
    with open(spawn_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                requests.append(json.loads(line))
    
    if requests:
        print(f"  待处理请求: {len(requests)}")
        for req in requests[-5:]:
            print(f"    {req.get('task_id')}: {req.get('label')} - {req.get('role', 'N/A')}")
    else:
        print("  无待处理请求")
else:
    print("🚀 Spawn 请求：无待处理请求")

print("\n=== 分析完成 ===")
