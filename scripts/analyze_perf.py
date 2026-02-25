import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 读取最近 7 天的事件
cutoff = (datetime.now() - timedelta(days=7)).isoformat()
events_file = Path("aios/events/events.jsonl")

if not events_file.exists():
    print("No events.jsonl found")
    exit(0)

events = []
with open(events_file, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                e = json.loads(line)
                if e.get("ts", "") > cutoff:
                    events.append(e)
            except:
                pass

print(f"Total events (7d): {len(events)}")

# 找出慢操作 (>5000ms = 5s)
slow_ops = [e for e in events if e.get("latency_ms", 0) > 5000]
print(f"\nSlow operations (>5s): {len(slow_ops)}")

# TOP 10 慢操作
slow_sorted = sorted(slow_ops, key=lambda x: x.get("latency_ms", 0), reverse=True)[:10]
print("\nTOP 10 slowest operations:")
for i, e in enumerate(slow_sorted, 1):
    latency_sec = e.get("latency_ms", 0) / 1000
    print(f"  {i}. {e.get('event')}: {latency_sec:.2f}s")
    if "payload" in e:
        print(f"     Payload: {str(e['payload'])[:100]}")

# 统计慢操作类型
slow_types = Counter([e.get("event") for e in slow_ops])
print("\nSlow operation types:")
for op_type, count in slow_types.most_common(5):
    print(f"  {op_type}: {count} times")

# 平均耗时 TOP 5
type_durations = {}
for e in events:
    if "latency_ms" in e:
        t = e.get("event")
        if t not in type_durations:
            type_durations[t] = []
        type_durations[t].append(e["latency_ms"])

avg_durations = {t: sum(d)/len(d) for t, d in type_durations.items()}
print("\nAverage latency TOP 5:")
for t, avg in sorted(avg_durations.items(), key=lambda x: x[1], reverse=True)[:5]:
    avg_sec = avg / 1000
    print(f"  {t}: {avg_sec:.2f}s (count: {len(type_durations[t])})")

# 错误事件统计
errors = [e for e in events if e.get("status") == "error"]
print(f"\nError events: {len(errors)}")
error_types = Counter([e.get("event") for e in errors])
print("Error types:")
for err_type, count in error_types.most_common(5):
    print(f"  {err_type}: {count} times")
