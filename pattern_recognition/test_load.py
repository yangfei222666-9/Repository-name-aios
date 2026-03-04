import json
from pathlib import Path
from datetime import datetime, timedelta

data_dir = Path("../agent_system")
tasks_file = data_dir / "task_queue.jsonl"

print(f"Tasks file: {tasks_file}")
print(f"Exists: {tasks_file.exists()}")

cutoff_time = datetime.now() - timedelta(hours=24)
print(f"Cutoff time: {cutoff_time}")

tasks = []

with open(tasks_file, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        try:
            task = json.loads(line)
            
            # 只处理已完成的任务
            if task.get("status") != "completed":
                print(f"[{i+1}] Skipped: status={task.get('status')}")
                continue
            
            # 检查时间
            updated_at = task.get("updated_at")
            if updated_at:
                task_time = datetime.fromtimestamp(updated_at)
                if task_time < cutoff_time:
                    print(f"[{i+1}] Skipped: too old ({task_time})")
                    continue
            else:
                print(f"[{i+1}] Skipped: no updated_at")
                continue
            
            # 提取关键信息
            result = task.get("result", {})
            timestamp = task_time if updated_at else datetime.now()
            
            # 计算成本
            tokens = result.get("tokens", {})
            input_tokens = tokens.get("input", 0)
            output_tokens = tokens.get("output", 0)
            cost = (input_tokens / 1000 * 0.003) + (output_tokens / 1000 * 0.015)
            
            tasks.append({
                "id": task.get("id"),
                "type": task.get("type"),
                "status": "completed",
                "success": result.get("success", True),
                "duration": result.get("duration", 0),
                "cost": cost,
                "tokens": tokens,
                "timestamp": timestamp.isoformat()
            })
            
            print(f"[{i+1}] Added: {task.get('id')[:20]}...")
            
        except Exception as e:
            print(f"[{i+1}] Error: {e}")
            continue

print(f"\nTotal tasks loaded: {len(tasks)}")
