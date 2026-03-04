#!/usr/bin/env python3
"""AIOS Dashboard Data Export Script"""
import json
import sys
from pathlib import Path
from datetime import datetime

def read_jsonl(file_path, limit=None):
    """Read JSONL file and return list of objects"""
    data = []
    if not file_path.exists():
        return data
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        if limit:
            lines = lines[-limit:]
        for line in lines:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return data

def read_json(file_path):
    """Read JSON file"""
    if not file_path.exists():
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return None

def main():
    base_dir = Path(r"C:\Users\A\.openclaw\workspace\aios\agent_system")
    output_path = Path(r"C:\Users\A\.openclaw\workspace\aios\dashboard\export_data.json")
    
    print("=== AIOS Data Export ===")
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    # 1. Agents
    agents_file = base_dir / "agents.json"
    print("[1/6] agents.json...", end=" ")
    agents = read_json(agents_file)
    if agents:
        export_data["agents"] = agents
        print(f"OK ({len(agents.get('agents', []))} agents)")
    else:
        print("SKIP")
    
    # 2. Tasks
    queue_file = base_dir / "task_queue.jsonl"
    print("[2/6] task_queue.jsonl...", end=" ")
    tasks = read_jsonl(queue_file)
    export_data["tasks"] = tasks
    print(f"OK ({len(tasks)} tasks)")
    
    # 3. Events (last 1000)
    events_file = base_dir / "events.jsonl"
    print("[3/6] events.jsonl...", end=" ")
    events = read_jsonl(events_file, limit=1000)
    export_data["events"] = events
    print(f"OK ({len(events)} events)")
    
    # 4. Lessons
    lessons_file = base_dir / "lessons.json"
    print("[4/6] lessons.json...", end=" ")
    lessons = read_json(lessons_file)
    if lessons:
        export_data["lessons"] = lessons
        print("OK")
    else:
        print("SKIP")
    
    # 5. Alerts
    alerts_file = base_dir / "alerts.jsonl"
    print("[5/6] alerts.jsonl...", end=" ")
    alerts = read_jsonl(alerts_file)
    export_data["alerts"] = alerts
    print(f"OK ({len(alerts)} alerts)")
    
    # 6. System State
    state_file = base_dir / "system_state.json"
    print("[6/6] system_state.json...", end=" ")
    state = read_json(state_file)
    if state:
        export_data["system_state"] = state
        print("OK")
    else:
        print("SKIP")
    
    # Write export file
    print(f"\nWriting to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    file_size = output_path.stat().st_size / 1024
    print(f"Done! ({file_size:.2f} KB)")

if __name__ == "__main__":
    main()
