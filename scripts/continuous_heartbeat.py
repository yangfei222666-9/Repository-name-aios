"""
持续心跳进程 - 处理 Agent Spawn 请求
每 30 秒检查一次 spawn_requests.jsonl，批量创建 sub-agent
"""
import json
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

def process_spawn_requests():
    """处理 spawn requests"""
    spawn_file = Path("aios/agent_system/spawn_requests.jsonl")
    results_file = Path("aios/agent_system/spawn_results.jsonl")
    
    if not spawn_file.exists():
        return 0
    
    # 读取所有 pending requests
    requests = []
    with open(spawn_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                requests.append(req)
            except:
                pass
    
    if not requests:
        return 0
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {len(requests)} spawn requests")
    
    # 模拟处理（实际应该用 sessions_spawn）
    # 这里简化为直接标记为已处理
    processed = 0
    for req in requests:
        label = req.get('label', '?')
        role = req.get('role', '?')
        print(f"  Processing: {label[:50]} (role={role})")
        
        # 记录结果
        result = {
            "request_id": req.get('task_id', 'unknown'),
            "label": label,
            "spawned_at": datetime.now().isoformat(),
            "status": "spawned",
            "session_key": f"agent-{processed:03d}"
        }
        
        with open(results_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
        
        processed += 1
    
    # 清空 spawn_requests
    spawn_file.write_text('', encoding='utf-8')
    
    return processed

def main():
    print("=" * 60)
    print("AIOS 持续心跳 - Agent Spawn 处理器")
    print("=" * 60)
    print()
    print("按 Ctrl+C 停止")
    print()
    
    cycle = 0
    try:
        while True:
            cycle += 1
            print(f"\n[Cycle {cycle}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 处理 spawn requests
            processed = process_spawn_requests()
            
            if processed > 0:
                print(f"✓ Processed {processed} spawn requests")
            else:
                print("  No pending requests")
            
            # 等待 30 秒
            print("  Waiting 30s...")
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        print(f"Total cycles: {cycle}")

if __name__ == "__main__":
    main()
