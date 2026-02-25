#!/usr/bin/env python3
"""
生成测试 Reactor 触发事件
"""

import json
from pathlib import Path
from datetime import datetime

AIOS_ROOT = Path(__file__).parent
EVENTS_FILE = AIOS_ROOT / "events" / "events.jsonl"

# 生成一个 CPU 高负载事件
test_event = {
    "ts": datetime.now().isoformat(),
    "epoch": int(datetime.now().timestamp()),
    "layer": "TOOL",
    "event": "cpu_high",
    "status": "warn",
    "severity": "WARN",
    "payload": {
        "message": "CPU usage 85% - high load detected",
        "cpu_percent": 85
    }
}

EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(EVENTS_FILE, 'a', encoding='utf-8') as f:
    f.write(json.dumps(test_event, ensure_ascii=False) + '\n')

print(f"✅ 生成测试事件: cpu_high (85%)")
print(f"📝 事件已写入: {EVENTS_FILE}")
print(f"\n现在运行 Reactor 自动触发器:")
print(f"python reactor_auto_trigger.py")
