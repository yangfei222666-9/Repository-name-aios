"""
正确触发 Meta-Agent 缺口检测
使用正确的字段格式
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

traces_file = Path("aios/agent_system/data/traces/agent_traces.jsonl")

# 创建符合 Meta-Agent 检测格式的失败 trace
fake_traces = []
now = datetime.now()

# 场景 1：代码任务频繁失败（需要 coder Agent）
for i in range(5):
    trace = {
        "trace_id": f"meta_trigger_code_{i}",
        "agent_id": "dispatcher",
        "task": f"代码开发任务 {i}",
        "task_type": "code",
        "timestamp": (now - timedelta(hours=i)).isoformat(),
        "start_time": (now - timedelta(hours=i)).isoformat(),
        "end_time": (now - timedelta(hours=i) + timedelta(seconds=30)).isoformat(),
        "duration_sec": 30.0,
        "status": "failed",  # Meta-Agent 检查这个字段
        "success": False,
        "error": "No suitable coder agent available",
        "env": "prod"
    }
    fake_traces.append(trace)

# 场景 2：分析任务频繁失败（需要 analyst Agent）
for i in range(4):
    trace = {
        "trace_id": f"meta_trigger_analysis_{i}",
        "agent_id": "dispatcher",
        "task": f"数据分析任务 {i}",
        "task_type": "analysis",
        "timestamp": (now - timedelta(hours=i)).isoformat(),
        "start_time": (now - timedelta(hours=i)).isoformat(),
        "end_time": (now - timedelta(hours=i) + timedelta(seconds=25)).isoformat(),
        "duration_sec": 25.0,
        "status": "failed",
        "success": False,
        "error": "No suitable analyst agent available",
        "env": "prod"
    }
    fake_traces.append(trace)

# 场景 3：监控任务频繁失败（需要 monitor Agent）
for i in range(3):
    trace = {
        "trace_id": f"meta_trigger_monitor_{i}",
        "agent_id": "dispatcher",
        "task": f"系统监控任务 {i}",
        "task_type": "monitor",
        "timestamp": (now - timedelta(hours=i)).isoformat(),
        "start_time": (now - timedelta(hours=i)).isoformat(),
        "end_time": (now - timedelta(hours=i) + timedelta(seconds=20)).isoformat(),
        "duration_sec": 20.0,
        "status": "failed",
        "success": False,
        "error": "No suitable monitor agent available",
        "env": "prod"
    }
    fake_traces.append(trace)

# 写入
with open(traces_file, 'a', encoding='utf-8') as f:
    for trace in fake_traces:
        f.write(json.dumps(trace, ensure_ascii=False) + '\n')

print(f"✓ 已创建 {len(fake_traces)} 个失败 trace（符合 Meta-Agent 检测格式）")
print()
print("失败场景：")
print("  - 5 个代码任务失败 → 需要 coder Agent")
print("  - 4 个分析任务失败 → 需要 analyst Agent")
print("  - 3 个监控任务失败 → 需要 monitor Agent")
print()
print("现在运行 Meta-Agent 检测：")
print("  python aios/agent_system/meta_agent.py heartbeat")
