#!/usr/bin/env python3
"""
生成测试事件，用于验证 Reactor 自动触发
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).parent
EVENTS_FILE = AIOS_ROOT / "events" / "events.jsonl"

# 生成测试事件
test_events = [
    {
        "ts": datetime.now().isoformat(),
        "epoch": int(datetime.now().timestamp()),
        "layer": "TOOL",
        "event": "network_error",
        "status": "err",
        "severity": "ERR",
        "payload": {
            "error": "502 Bad Gateway - connection timeout"
        }
    },
    {
        "ts": datetime.now().isoformat(),
        "epoch": int(datetime.now().timestamp()),
        "layer": "TOOL",
        "event": "api_error",
        "status": "err",
        "severity": "WARN",
        "payload": {
            "error": "429 Too Many Requests - rate limit exceeded"
        }
    },
    {
        "ts": datetime.now().isoformat(),
        "epoch": int(datetime.now().timestamp()),
        "layer": "TOOL",
        "event": "high_latency",
        "status": "ok",
        "severity": "WARN",
        "latency_ms": 5000,
        "payload": {
            "message": "Request took 5000ms, threshold is 1000ms"
        }
    }
]

# 写入事件
EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(EVENTS_FILE, 'a', encoding='utf-8') as f:
    for event in test_events:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')

print(f"✅ 生成了 {len(test_events)} 个测试事件")
print("📝 事件类型:")
for event in test_events:
    print(f"  - {event['event']} ({event['severity']})")
