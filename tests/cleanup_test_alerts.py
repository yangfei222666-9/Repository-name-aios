"""清理测试告警"""

import sys

sys.path.insert(0, r"C:\Users\A\.openclaw\workspace\scripts")
import alert_fsm

# 查看当前告警
stats = alert_fsm.stats()
print(f"当前告警状态：")
print(f"  OPEN: {stats.get('open', 0)}")
print(f"  ACK: {stats.get('ack', 0)}")
print(f"  RESOLVED: {stats.get('resolved_today', 0)}")

# 列出所有 OPEN 告警
alerts = alert_fsm.load_active()
open_alerts = [(k, v) for k, v in alerts.items() if v.get("status") == "OPEN"]

print(f"\n待清理的测试告警：")
for fp, alert in open_alerts:
    if "test" in alert.get("scope", ""):
        print(f"  - {alert['id']}: {alert['rule_id']} ({alert['message'][:50]})")
        # 解决测试告警
        alert_fsm.resolve_alert(alert["id"], "测试完成，清理")

# 再次检查
stats = alert_fsm.stats()
print(f"\n清理后状态：")
print(f"  OPEN: {stats.get('open', 0)}")
print(f"  RESOLVED: {stats.get('resolved_today', 0)}")
