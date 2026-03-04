import json
from pathlib import Path
from datetime import datetime, timedelta

tasks_file = Path("../agent_system/task_queue.jsonl")
print(f"File exists: {tasks_file.exists()}")

if tasks_file.exists():
    with open(tasks_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    
    cutoff_time = datetime.now() - timedelta(hours=24)
    completed_count = 0
    recent_count = 0
    
    for i, line in enumerate(lines[:10]):
        task = json.loads(line)
        status = task.get('status')
        updated_at = task.get('updated_at')
        
        if status == 'completed':
            completed_count += 1
        
        if updated_at:
            task_time = datetime.fromtimestamp(updated_at)
            if task_time >= cutoff_time:
                recent_count += 1
        
        print(f"[{i+1}] ID: {task.get('id')[:20]}..., status: {status}, updated_at: {updated_at}")
    
    print(f"\nCompleted in first 10: {completed_count}")
    print(f"Recent (24h) in first 10: {recent_count}")
