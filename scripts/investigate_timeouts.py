import json
from pathlib import Path
from collections import Counter

events_file = Path("aios/events/events.jsonl")
events = []
with open(events_file, encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                events.append(json.loads(line))
            except:
                pass

# 找出所有超时相关事件
timeouts = [e for e in events if 'timeout' in e.get('event', '').lower() or 
            e.get('payload', {}).get('trigger') == 'task.timeout']

print(f"Total timeout events: {len(timeouts)}\n")

# 按事件类型分组
timeout_types = Counter([e.get('event') for e in timeouts])
print("Timeout event types:")
for t, count in timeout_types.items():
    print(f"  {t}: {count} times")

# 详细信息
print("\nDetailed timeout events (last 10):")
for i, e in enumerate(timeouts[-10:], 1):
    print(f"\n{i}. Event: {e.get('event')}")
    print(f"   Time: {e.get('ts')}")
    print(f"   Status: {e.get('status')}")
    print(f"   Payload: {e.get('payload')}")
    
# 找出触发 Reactor 的超时
reactor_timeout_triggers = [e for e in events if 
                            e.get('event') == 'reactor.auto_fix.failed' and
                            e.get('payload', {}).get('trigger') == 'task.timeout']

print(f"\n\nReactor triggered by task.timeout: {len(reactor_timeout_triggers)}")
for i, e in enumerate(reactor_timeout_triggers, 1):
    print(f"\n{i}. Time: {e.get('ts')}")
    print(f"   Action: {e.get('payload', {}).get('action')}")
    print(f"   Verified: {e.get('payload', {}).get('verified')}")
    print(f"   Duration: {e.get('payload', {}).get('duration_ms')}ms")
