# aios/plugin_heartbeat.py - 插件系统心跳
"""
每次心跳运行，初始化插件系统并发布心跳事件
"""
import sys
from pathlib import Path
import json
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
AIOS_ROOT = Path(__file__).parent
sys.path.insert(0, str(AIOS_ROOT))

from plugins.manager import get_manager
from plugins.eventbus import get_bus


def main():
    manager = get_manager()
    bus = get_bus()

    # 统计
    alerts = []
    
    # 1. 确保关键插件已加载
    critical_plugins = [
        "builtin/notifier_telegram",
        "builtin/sensor_resource",
    ]
    
    for plugin_name in critical_plugins:
        if plugin_name not in manager.plugins:
            try:
                manager.load(plugin_name)
            except Exception as e:
                alerts.append(f"加载插件 {plugin_name} 失败: {e}")
    
    # 2. 运行 Sensor 插件采集数据
    for name, plugin in manager.plugins.items():
        meta = plugin.meta()
        if meta.plugin_type.value == "sensor":
            try:
                events = plugin.collect()
                for event in events:
                    # 发布到 EventBus
                    bus.publish(event.get("topic", "event.sensor"), event)
                    
                    # 检查告警
                    if event.get("severity") in ("warn", "error", "critical"):
                        alerts.append(f"{event.get('category')}: {event.get('data', {}).get('alerts', [])}")
            except Exception as e:
                alerts.append(f"Sensor {name} 采集失败: {e}")
    
    # 3. 发布心跳事件
    heartbeat_event = {
        "timestamp": int(datetime.now().timestamp()),
        "topic": "heartbeat.tick",
        "type": "heartbeat",
        "data": {
            "plugins_loaded": len(manager.plugins),
            "alerts": len(alerts),
        }
    }
    bus.publish("heartbeat.tick", heartbeat_event)
    
    # 4. 更新时间戳
    state_file = Path(r"C:\Users\A\.openclaw\workspace\memory\selflearn-state.json")
    state = {}
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
    
    state["last_plugin_heartbeat"] = datetime.now().isoformat()
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    # 5. 输出结果
    if alerts:
        print(f"PLUGIN_ALERTS:{len(alerts)}")
        for alert in alerts[:3]:  # 最多显示3个
            print(f"  - {alert}")
    else:
        print("PLUGIN_OK")


if __name__ == "__main__":
    main()
