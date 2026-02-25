"""测试新的事件存储系统"""
import sys
sys.path.insert(0, r"C:\Users\A\.openclaw\workspace\aios")

from core.event import Event, EventType
from core.event_bus import get_event_bus

# 创建测试事件
bus = get_event_bus()

# 发布几个测试事件
for i in range(5):
    event = Event.create(
        event_type=EventType.AGENT_TASK_COMPLETED,
        source="test",
        payload={"task_id": i, "result": "success"}
    )
    bus.emit(event)
    print(f"[测试] 发布事件 {i+1}/5")

# 加载事件
events = bus.load_events(limit=10)
print(f"\n[测试] 加载到 {len(events)} 个事件")

# 检查文件
from pathlib import Path
from datetime import datetime

events_dir = Path(r"C:\Users\A\.openclaw\workspace\aios\data\events")
today = datetime.now().strftime("%Y-%m-%d")
today_file = events_dir / f"{today}.jsonl"

if today_file.exists():
    size = today_file.stat().st_size
    print(f"[测试] 今天的文件：{today_file.name} ({size} bytes)")
else:
    print(f"[测试] 今天的文件不存在：{today_file}")

print("\n[测试] 完成！")
