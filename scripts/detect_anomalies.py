import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

# 读取最近 24h 的事件
cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
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

print(f"Total events (24h): {len(events)}")

# 1. 频繁失败（同一事件类型失败 ≥3 次）
errors = [e for e in events if e.get("status") == "error"]
error_types = Counter([e.get("event") for e in errors])
frequent_failures = {k: v for k, v in error_types.items() if v >= 3}

print(f"\n[CRITICAL] Frequent failures (>=3 times):")
for err_type, count in sorted(frequent_failures.items(), key=lambda x: x[1], reverse=True):
    print(f"  {err_type}: {count} times")
    # 找出最近一次失败的详情
    last_error = [e for e in errors if e.get("event") == err_type][-1]
    print(f"    Last: {last_error.get('ts')}")
    print(f"    Payload: {str(last_error.get('payload', {}))[:100]}")

# 2. 资源峰值（latency >1000ms）
high_latency = [e for e in events if e.get("latency_ms", 0) > 1000]
print(f"\n[WARNING] High latency events (>1s): {len(high_latency)}")
latency_types = Counter([e.get("event") for e in high_latency])
for lat_type, count in latency_types.most_common(5):
    print(f"  {lat_type}: {count} times")

# 3. 超时事件
timeouts = [e for e in events if "timeout" in e.get("event", "").lower()]
print(f"\n[TIMEOUT] Timeout events: {len(timeouts)}")
for t in timeouts[:5]:
    print(f"  {t.get('event')}: {t.get('ts')}")
    print(f"    Payload: {str(t.get('payload', {}))[:100]}")

# 4. 异常模式识别
print(f"\n[ANALYSIS] Anomaly patterns:")

# 4.1 错误率
error_rate = len(errors) / len(events) * 100 if events else 0
print(f"  Error rate: {error_rate:.1f}% ({len(errors)}/{len(events)})")
if error_rate > 10:
    print(f"    [WARNING] High error rate (>10%)")

# 4.2 Reactor 失败率
reactor_events = [e for e in events if "reactor" in e.get("event", "")]
reactor_failures = [e for e in reactor_events if e.get("status") == "error"]
reactor_fail_rate = len(reactor_failures) / len(reactor_events) * 100 if reactor_events else 0
print(f"  Reactor failure rate: {reactor_fail_rate:.1f}% ({len(reactor_failures)}/{len(reactor_events)})")
if reactor_fail_rate > 20:
    print(f"    [WARNING] High reactor failure rate (>20%)")

# 4.3 Scheduler 决策延迟
scheduler_events = [e for e in events if "scheduler" in e.get("event", "")]
if scheduler_events:
    avg_latency = sum(e.get("latency_ms", 0) for e in scheduler_events) / len(scheduler_events)
    print(f"  Scheduler avg latency: {avg_latency:.0f}ms")
    if avg_latency > 500:
        print(f"    [WARNING] High scheduler latency (>500ms)")

print(f"\n[OK] Analysis complete")
